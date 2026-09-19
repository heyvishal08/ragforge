"""Analytics API endpoints — observability and query metrics."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.workspace import get_current_workspace
from app.models.workspace import Workspace
from app.models.query_log import QueryLog
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.knowledge_base import KnowledgeBase
from app.schemas import AnalyticsSummary, QueryLogResponse

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    knowledge_base_id: Optional[uuid.UUID] = None,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated analytics summary scoped to visitor's workspace."""
    workspace_kb_ids = select(KnowledgeBase.id).where(KnowledgeBase.workspace_id == workspace.id)
    
    # Total queries
    q = select(func.count(QueryLog.id)).where(QueryLog.knowledge_base_id.in_(workspace_kb_ids))
    if knowledge_base_id:
        q = q.where(QueryLog.knowledge_base_id == knowledge_base_id)
    total_queries = (await db.execute(q)).scalar() or 0
    
    # Average latency
    q = select(func.avg(QueryLog.total_latency_ms)).where(QueryLog.knowledge_base_id.in_(workspace_kb_ids))
    if knowledge_base_id:
        q = q.where(QueryLog.knowledge_base_id == knowledge_base_id)
    avg_latency = (await db.execute(q)).scalar() or 0
    
    # Success rate
    result = await db.execute(
        select(
            func.count(QueryLog.id).filter(QueryLog.success == True),
            func.count(QueryLog.id),
        ).where(QueryLog.knowledge_base_id.in_(workspace_kb_ids))
    )
    success_count, total = result.one()
    success_rate = (success_count / total * 100) if total > 0 else 100
    
    # Document and chunk counts
    total_documents = (
        await db.execute(
            select(func.count(Document.id)).where(Document.knowledge_base_id.in_(workspace_kb_ids))
        )
    ).scalar() or 0
    
    total_chunks = (
        await db.execute(
            select(func.count(DocumentChunk.id))
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.knowledge_base_id.in_(workspace_kb_ids))
        )
    ).scalar() or 0
    
    total_kbs = (
        await db.execute(
            select(func.count(KnowledgeBase.id)).where(KnowledgeBase.workspace_id == workspace.id)
        )
    ).scalar() or 0
    
    # Recent queries
    recent_result = await db.execute(
        select(QueryLog)
        .where(QueryLog.knowledge_base_id.in_(workspace_kb_ids))
        .order_by(desc(QueryLog.created_at))
        .limit(20)
    )
    recent = recent_result.scalars().all()
    
    return AnalyticsSummary(
        total_queries=total_queries,
        avg_latency_ms=round(avg_latency, 2),
        success_rate=round(success_rate, 2),
        total_documents=total_documents,
        total_chunks=total_chunks,
        total_knowledge_bases=total_kbs,
        recent_queries=[QueryLogResponse.model_validate(q) for q in recent],
    )


@router.get("/queries", response_model=list[QueryLogResponse])
async def list_query_logs(
    knowledge_base_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """List query logs scoped to the current visitor's workspace."""
    workspace_kb_ids = select(KnowledgeBase.id).where(KnowledgeBase.workspace_id == workspace.id)
    
    query = (
        select(QueryLog)
        .where(QueryLog.knowledge_base_id.in_(workspace_kb_ids))
        .order_by(desc(QueryLog.created_at))
        .limit(limit)
    )
    if knowledge_base_id:
        query = query.where(QueryLog.knowledge_base_id == knowledge_base_id)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    return [QueryLogResponse.model_validate(q) for q in logs]
