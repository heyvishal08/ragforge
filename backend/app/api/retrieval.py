"""Retrieval API endpoints — search and compare strategies."""

import uuid
import time

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.schemas import RetrievalRequest, RetrievalResponse, RetrievalResult

logger = structlog.get_logger()

router = APIRouter()


@router.post("/search", response_model=RetrievalResponse)
async def search(
    request: RetrievalRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run retrieval with configurable strategy.
    Used by both the chat endpoint and the Retrieval Playground.
    """
    from app.rag.retrieval.hybrid import HybridRetriever
    from app.rag.reranker import get_reranker
    from app.providers.embedding_provider import get_embedding_provider
    
    # Validate knowledge base
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == request.knowledge_base_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    embedding_provider = get_embedding_provider()
    retriever = HybridRetriever(db, embedding_provider)
    
    start = time.perf_counter()
    
    results = await retriever.search(
        query=request.query,
        knowledge_base_id=request.knowledge_base_id,
        strategy=request.strategy,
        top_k=request.top_k,
        document_ids=request.document_ids,
    )
    
    retrieval_time = (time.perf_counter() - start) * 1000
    
    # Optionally rerank
    if request.rerank and results:
        reranker = get_reranker()
        rerank_start = time.perf_counter()
        results = await reranker.rerank(request.query, results)
        rerank_time = (time.perf_counter() - rerank_start) * 1000
    else:
        rerank_time = 0
    
    return RetrievalResponse(
        results=[
            RetrievalResult(
                chunk_id=r["chunk_id"],
                document_name=r["document_name"],
                page_number=r.get("page_number"),
                content=r["content"],
                score=r["score"],
                retrieval_method=r["retrieval_method"],
                rerank_score=r.get("rerank_score"),
            )
            for r in results
        ],
        metadata={
            "strategy": request.strategy,
            "reranked": request.rerank,
            "total_results": len(results),
            "retrieval_latency_ms": round(retrieval_time, 2),
            "rerank_latency_ms": round(rerank_time, 2),
        },
    )
