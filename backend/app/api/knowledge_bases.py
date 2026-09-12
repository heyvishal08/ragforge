"""Knowledge Bases API endpoints."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.workspace import Workspace
from app.models.user import User
from app.models.document import Document
from app.schemas import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse

router = APIRouter()


async def _ensure_default_user_and_workspace(db: AsyncSession):
    """Ensure a default user and workspace exist (single-user mode)."""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email="user@ragforge.dev", name="RAGForge User")
        db.add(user)
        await db.flush()
        workspace = Workspace(user_id=user.id, name="Default Workspace")
        db.add(workspace)
        await db.flush()
        return workspace
    result = await db.execute(
        select(Workspace).where(Workspace.user_id == user.id).limit(1)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        workspace = Workspace(user_id=user.id, name="Default Workspace")
        db.add(workspace)
        await db.flush()
    return workspace


@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(db: AsyncSession = Depends(get_db)):
    """List all knowledge bases."""
    workspace = await _ensure_default_user_and_workspace(db)
    
    result = await db.execute(
        select(
            KnowledgeBase,
            func.count(Document.id).label("document_count")
        )
        .outerjoin(Document, Document.knowledge_base_id == KnowledgeBase.id)
        .where(KnowledgeBase.workspace_id == workspace.id)
        .group_by(KnowledgeBase.id)
        .order_by(KnowledgeBase.created_at.desc())
    )
    
    kbs = []
    for kb, doc_count in result.all():
        kbs.append(KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=doc_count,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
        ))
    return kbs


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base."""
    workspace = await _ensure_default_user_and_workspace(db)
    
    kb = KnowledgeBase(
        workspace_id=workspace.id,
        name=data.name,
        description=data.description,
    )
    db.add(kb)
    await db.flush()
    await db.refresh(kb)
    
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        document_count=0,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific knowledge base."""
    result = await db.execute(
        select(
            KnowledgeBase,
            func.count(Document.id).label("document_count")
        )
        .outerjoin(Document, Document.knowledge_base_id == KnowledgeBase.id)
        .where(KnowledgeBase.id == kb_id)
        .group_by(KnowledgeBase.id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    kb, doc_count = row
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        document_count=doc_count,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: uuid.UUID,
    data: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a knowledge base."""
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    if data.name is not None:
        kb.name = data.name
    if data.description is not None:
        kb.description = data.description
    
    await db.flush()
    await db.refresh(kb)
    
    doc_result = await db.execute(
        select(func.count(Document.id)).where(Document.knowledge_base_id == kb_id)
    )
    doc_count = doc_result.scalar() or 0
    
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        document_count=doc_count,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(kb_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a knowledge base and all its documents."""
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    await db.delete(kb)
