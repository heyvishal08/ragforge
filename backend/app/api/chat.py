"""Chat API endpoints — streaming generation with citations."""

import json
import uuid
import time
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.workspace import get_current_workspace
from app.models.workspace import Workspace
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.citation import Citation
from app.models.knowledge_base import KnowledgeBase
from app.schemas import (
    ChatRequest, ChatResponse, CitationResponse,
    ConversationResponse, MessageResponse,
)

logger = structlog.get_logger()

router = APIRouter()


@router.post("")
async def chat(
    request: ChatRequest,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """
    Process a chat query through the full RAG pipeline:
    Query → Router → Retrieval → Reranking → Generation → Citations
    
    Returns a streaming SSE response.
    """
    from app.rag.pipeline import RAGPipeline
    
    # Validate knowledge base belongs to current workspace
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == request.knowledge_base_id,
            KnowledgeBase.workspace_id == workspace.id,
        )
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found in your workspace")
    
    # Get or create conversation
    if request.conversation_id:
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == request.conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            knowledge_base_id=request.knowledge_base_id,
            title=request.query[:100],
        )
        db.add(conversation)
        await db.flush()
    
    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.query,
    )
    db.add(user_msg)
    await db.flush()
    
    # Run RAG pipeline
    pipeline = RAGPipeline(db)
    
    async def generate_stream():
        try:
            rag_result = await pipeline.run(
                query=request.query,
                knowledge_base_id=request.knowledge_base_id,
                retrieval_strategy=request.retrieval_strategy,
                document_ids=request.document_ids,
            )
            
            # Save assistant message
            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=rag_result["answer"],
                retrieval_metadata=rag_result["retrieval_metadata"],
                token_count=rag_result.get("token_count"),
                latency_ms=rag_result.get("total_latency_ms"),
            )
            db.add(assistant_msg)
            await db.flush()
            
            # Save citations
            citations_data = []
            for i, cit in enumerate(rag_result.get("citations", [])):
                citation = Citation(
                    message_id=assistant_msg.id,
                    chunk_id=cit["chunk_id"],
                    citation_index=i + 1,
                    relevance_score=cit.get("relevance_score"),
                    rerank_score=cit.get("rerank_score"),
                    retrieval_method=cit.get("retrieval_method"),
                )
                db.add(citation)
                citations_data.append({
                    "id": str(citation.id),
                    "citation_index": i + 1,
                    "document_name": cit.get("document_name", ""),
                    "page_number": cit.get("page_number"),
                    "chunk_content": cit.get("chunk_content", ""),
                    "relevance_score": cit.get("relevance_score"),
                    "rerank_score": cit.get("rerank_score"),
                    "retrieval_method": cit.get("retrieval_method"),
                })
            
            await db.commit()
            
            # Stream: first send the answer content
            yield f"data: {json.dumps({'type': 'content', 'content': rag_result['answer']})}\n\n"
            
            # Then send citations
            yield f"data: {json.dumps({'type': 'citations', 'citations': citations_data})}\n\n"
            
            # Then send metadata
            yield f"data: {json.dumps({'type': 'metadata', 'retrieval_metadata': rag_result['retrieval_metadata'], 'confidence': rag_result.get('confidence'), 'conversation_id': str(conversation.id), 'message_id': str(assistant_msg.id)})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error("Chat pipeline error", error=str(e))
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    knowledge_base_id: Optional[uuid.UUID] = None,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """List conversations scoped to visitor's workspace."""
    query = (
        select(Conversation)
        .join(KnowledgeBase, KnowledgeBase.id == Conversation.knowledge_base_id)
        .where(KnowledgeBase.workspace_id == workspace.id)
        .order_by(Conversation.updated_at.desc())
    )
    if knowledge_base_id:
        query = query.where(Conversation.knowledge_base_id == knowledge_base_id)
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    response = []
    for conv in conversations:
        msg_count_result = await db.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conv.id)
        )
        msg_count = msg_count_result.scalar() or 0
        response.append(ConversationResponse(
            id=conv.id,
            knowledge_base_id=conv.knowledge_base_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count,
        ))
    return response


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(
    conv_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a conversation with citations (scoped to current workspace)."""
    result = await db.execute(
        select(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .join(KnowledgeBase, KnowledgeBase.id == Conversation.knowledge_base_id)
        .options(selectinload(Message.citations))
        .where(Message.conversation_id == conv_id, KnowledgeBase.workspace_id == workspace.id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    response = []
    for msg in messages:
        citations = []
        for cit in msg.citations:
            # Load chunk info for citation
            from app.models.document_chunk import DocumentChunk
            from app.models.document import Document
            chunk_result = await db.execute(
                select(DocumentChunk, Document.filename)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(DocumentChunk.id == cit.chunk_id)
            )
            chunk_row = chunk_result.one_or_none()
            if chunk_row:
                chunk, doc_name = chunk_row
                citations.append(CitationResponse(
                    id=cit.id,
                    citation_index=cit.citation_index,
                    document_name=doc_name,
                    page_number=chunk.page_number,
                    chunk_content=chunk.content[:500],
                    relevance_score=cit.relevance_score,
                    rerank_score=cit.rerank_score,
                    retrieval_method=cit.retrieval_method,
                ))
        
        response.append(MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            citations=citations,
            retrieval_metadata=msg.retrieval_metadata,
            latency_ms=msg.latency_ms,
            created_at=msg.created_at,
        ))
    return response
