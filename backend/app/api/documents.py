"""Documents API endpoints — upload, list, detail, delete."""

import os
import uuid
from typing import List, Optional

import aiofiles
import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db, async_session
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.knowledge_base import KnowledgeBase
from app.schemas import DocumentResponse, DocumentChunkResponse

logger = structlog.get_logger()

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/markdown": "md",
    "text/csv": "csv",
    "application/csv": "csv",
}

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md", "csv"}


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    knowledge_base_id: uuid.UUID = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document to a knowledge base for processing."""
    # Validate knowledge base exists
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Validate file extension
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read and validate file size
    content = await file.read()
    file_size = len(content)
    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size / 1024 / 1024:.1f}MB. Maximum: {settings.max_file_size_mb}MB"
        )
    
    # Save file to disk
    upload_dir = os.path.join(settings.upload_dir, str(knowledge_base_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    file_id = uuid.uuid4()
    file_path = os.path.join(upload_dir, f"{file_id}.{ext}")
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    
    # Create document record
    doc = Document(
        id=file_id,
        knowledge_base_id=knowledge_base_id,
        filename=file.filename,
        file_type=ext,
        file_size=file_size,
        status="UPLOADING",
        metadata_={"file_path": file_path},
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    # Process small documents (< 5MB) directly so they are immediately READY
    if file_size <= 5 * 1024 * 1024:
        await process_document(str(doc.id), file_path)
        await db.refresh(doc)
    else:
        background_tasks.add_task(process_document, str(doc.id), file_path)
    
    return DocumentResponse(
        id=doc.id,
        knowledge_base_id=doc.knowledge_base_id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status,
        page_count=doc.page_count,
        chunk_count=doc.chunk_count,
        summary=doc.summary,
        topics=doc.topics,
        entities=doc.entities,
        suggested_questions=doc.suggested_questions,
        error_message=doc.error_message,
        created_at=doc.created_at,
        processed_at=doc.processed_at,
    )


async def process_document(document_id: str, file_path: str):
    """Background task to parse, chunk, embed, and index a document."""
    from app.ingestion.pipeline import IngestionPipeline
    
    async with async_session() as db:
        try:
            pipeline = IngestionPipeline(db)
            await pipeline.process(document_id, file_path)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error("Document processing failed", document_id=document_id, error=str(e))
            # Update document status to FAILED
            try:
                result = await db.execute(
                    select(Document).where(Document.id == uuid.UUID(document_id))
                )
                doc = result.scalar_one_or_none()
                if doc:
                    doc.status = "FAILED"
                    doc.error_message = str(e)
                    await db.commit()
            except Exception:
                pass


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    knowledge_base_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """List documents, optionally filtered by knowledge base."""
    query = select(Document).order_by(Document.created_at.desc())
    if knowledge_base_id:
        query = query.where(Document.knowledge_base_id == knowledge_base_id)
    
    result = await db.execute(query)
    docs = result.scalars().all()
    return [
        DocumentResponse(
            id=d.id,
            knowledge_base_id=d.knowledge_base_id,
            filename=d.filename,
            file_type=d.file_type,
            file_size=d.file_size,
            status=d.status,
            page_count=d.page_count,
            chunk_count=d.chunk_count,
            summary=d.summary,
            topics=d.topics,
            entities=d.entities,
            suggested_questions=d.suggested_questions,
            error_message=d.error_message,
            created_at=d.created_at,
            processed_at=d.processed_at,
        )
        for d in docs
    ]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific document with details."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        id=doc.id,
        knowledge_base_id=doc.knowledge_base_id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status,
        page_count=doc.page_count,
        chunk_count=doc.chunk_count,
        summary=doc.summary,
        topics=doc.topics,
        entities=doc.entities,
        suggested_questions=doc.suggested_questions,
        error_message=doc.error_message,
        created_at=doc.created_at,
        processed_at=doc.processed_at,
    )


@router.get("/{doc_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get all chunks for a document."""
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = result.scalars().all()
    return [
        DocumentChunkResponse(
            id=c.id,
            chunk_index=c.chunk_index,
            content=c.content,
            page_number=c.page_number,
            token_count=c.token_count,
            metadata_=c.metadata_,
        )
        for c in chunks
    ]


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a document and all its chunks and citations."""
    from app.models.document_chunk import DocumentChunk
    from app.models.citation import Citation
    from sqlalchemy import delete
    
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from disk
    file_path = (doc.metadata_ or {}).get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass
    
    try:
        # 1. Delete citations referencing any chunks belonging to this document
        chunk_subquery = select(DocumentChunk.id).where(DocumentChunk.document_id == doc_id)
        await db.execute(delete(Citation).where(Citation.chunk_id.in_(chunk_subquery)))
        
        # 2. Delete all chunks belonging to this document
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc_id))
        
        # 3. Delete the document itself
        await db.execute(delete(Document).where(Document.id == doc_id))
        
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error("Failed to delete document", doc_id=str(doc_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
