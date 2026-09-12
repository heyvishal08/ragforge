"""
Document ingestion pipeline — orchestrates parsing, chunking, embedding, and indexing.
"""

import uuid
import time
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.ingestion.parsers import parse_document
from app.ingestion.chunker import Chunker
from app.providers.embedding_provider import get_embedding_provider

logger = structlog.get_logger()


class IngestionPipeline:
    """Orchestrates the full document ingestion process."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_provider = get_embedding_provider()
        self.chunker = Chunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    
    async def process(self, document_id: str, file_path: str):
        """
        Full ingestion pipeline:
        1. Update status to PARSING
        2. Parse document → extract text + metadata
        3. Update status to CHUNKING
        4. Split into chunks with metadata
        5. Update status to EMBEDDING
        6. Generate embeddings for each chunk
        7. Update status to INDEXING
        8. Store chunks + embeddings
        9. Generate summary, topics, entities
        10. Update status to READY
        """
        doc_uuid = uuid.UUID(document_id)
        
        result = await self.db.execute(
            select(Document).where(Document.id == doc_uuid)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        
        try:
            # ─── PARSING ───
            doc.status = "PARSING"
            await self.db.flush()
            logger.info("Parsing document", doc_id=document_id, filename=doc.filename)
            
            parsed = parse_document(file_path, doc.file_type)
            doc.page_count = parsed.get("page_count")
            
            # ─── CHUNKING ───
            doc.status = "CHUNKING"
            await self.db.flush()
            logger.info("Chunking document", doc_id=document_id)
            
            chunks = self.chunker.chunk(
                text=parsed["text"],
                pages=parsed.get("pages"),
                metadata=parsed.get("metadata", {}),
            )
            
            doc.chunk_count = len(chunks)
            
            # ─── EMBEDDING ───
            doc.status = "EMBEDDING"
            await self.db.flush()
            logger.info("Generating embeddings", doc_id=document_id, chunk_count=len(chunks))
            
            texts = [c["content"] for c in chunks]
            embeddings = self.embedding_provider.embed_batch(texts)
            
            # ─── INDEXING ───
            doc.status = "INDEXING"
            await self.db.flush()
            logger.info("Storing chunks", doc_id=document_id)
            
            for i, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
                chunk = DocumentChunk(
                    document_id=doc_uuid,
                    chunk_index=i,
                    content=chunk_data["content"],
                    page_number=chunk_data.get("page_number"),
                    token_count=chunk_data.get("token_count"),
                    embedding=embedding,
                    metadata_=chunk_data.get("metadata"),
                )
                self.db.add(chunk)
            
            await self.db.flush()
            
            # Update tsvector for keyword search
            await self.db.execute(
                text("""
                    UPDATE document_chunks 
                    SET search_vector = to_tsvector('english', content)
                    WHERE document_id = :doc_id AND search_vector IS NULL
                """),
                {"doc_id": str(doc_uuid)},
            )
            
            # ─── SUMMARY GENERATION ───
            await self._generate_summary(doc, chunks)
            
            # ─── DONE ───
            doc.status = "READY"
            doc.processed_at = datetime.now(timezone.utc)
            await self.db.flush()
            
            logger.info(
                "Document processing complete",
                doc_id=document_id,
                chunks=len(chunks),
                pages=doc.page_count,
            )
            
        except Exception as e:
            doc.status = "FAILED"
            doc.error_message = str(e)
            await self.db.flush()
            logger.error("Ingestion failed", doc_id=document_id, error=str(e))
            raise
    
    async def _generate_summary(self, doc: Document, chunks: list):
        """Generate document summary, topics, entities, and suggested questions using Groq."""
        from app.providers.llm_provider import get_llm_provider
        
        try:
            llm = get_llm_provider()
            
            # Use first few chunks for summary
            sample_text = "\n\n".join([c["content"] for c in chunks[:10]])[:4000]
            
            prompt = f"""Analyze this document excerpt and provide a JSON response with:
1. "summary": A concise 2-3 sentence summary
2. "topics": A list of 3-7 key topics (strings)
3. "entities": A list of 3-7 important entities (people, companies, technologies, etc.)
4. "suggested_questions": A list of 3-5 questions a reader might ask about this document

Document: {doc.filename}

Text excerpt:
{sample_text}

Respond with ONLY valid JSON, no markdown formatting."""
            
            response = await llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )
            
            import json
            # Try to parse JSON from response
            content = response["content"].strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            
            data = json.loads(content)
            doc.summary = data.get("summary", "")
            doc.topics = data.get("topics", [])
            doc.entities = data.get("entities", [])
            doc.suggested_questions = data.get("suggested_questions", [])
            
        except Exception as e:
            logger.warning("Summary generation failed, continuing", error=str(e))
            doc.summary = f"Document: {doc.filename} ({doc.chunk_count} chunks)"
