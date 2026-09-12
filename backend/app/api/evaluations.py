"""Evaluations API endpoints."""

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session
from app.models.evaluation import EvaluationRun, EvaluationQuestion
from app.models.knowledge_base import KnowledgeBase
from app.schemas import EvaluationRunCreate, EvaluationRunResponse

logger = structlog.get_logger()

router = APIRouter()


@router.post("", response_model=EvaluationRunResponse, status_code=201)
async def create_evaluation(
    data: EvaluationRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create and start an evaluation run."""
    # Validate KB
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == data.knowledge_base_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    run = EvaluationRun(
        knowledge_base_id=data.knowledge_base_id,
        name=data.name,
        status="PENDING",
        total_questions=len(data.questions),
    )
    db.add(run)
    await db.flush()
    
    # Create question records
    for q in data.questions:
        eq = EvaluationQuestion(
            evaluation_run_id=run.id,
            question=q.question,
            expected_answer=q.expected_answer,
            expected_sources=q.expected_sources,
        )
        db.add(eq)
    
    await db.flush()
    await db.refresh(run)
    
    # Run evaluation in background
    background_tasks.add_task(run_evaluation, str(run.id))
    
    return EvaluationRunResponse.model_validate(run)


async def run_evaluation(run_id: str):
    """Background task to execute evaluation."""
    from app.evaluation.evaluator import Evaluator
    
    async with async_session() as db:
        try:
            evaluator = Evaluator(db)
            await evaluator.run(run_id)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error("Evaluation failed", run_id=run_id, error=str(e))
            try:
                result = await db.execute(
                    select(EvaluationRun).where(EvaluationRun.id == uuid.UUID(run_id))
                )
                run = result.scalar_one_or_none()
                if run:
                    run.status = "FAILED"
                    await db.commit()
            except Exception:
                pass


@router.get("", response_model=List[EvaluationRunResponse])
async def list_evaluations(
    knowledge_base_id: uuid.UUID = None,
    db: AsyncSession = Depends(get_db),
):
    """List evaluation runs."""
    query = select(EvaluationRun).order_by(EvaluationRun.created_at.desc())
    if knowledge_base_id:
        query = query.where(EvaluationRun.knowledge_base_id == knowledge_base_id)
    
    result = await db.execute(query)
    runs = result.scalars().all()
    return [EvaluationRunResponse.model_validate(r) for r in runs]


@router.get("/{run_id}", response_model=EvaluationRunResponse)
async def get_evaluation(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get evaluation run details."""
    result = await db.execute(
        select(EvaluationRun).where(EvaluationRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return EvaluationRunResponse.model_validate(run)
