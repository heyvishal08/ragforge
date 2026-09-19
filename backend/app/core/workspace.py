"""
Workspace and session resolution utilities.
Enables multi-tenant session isolation so each visitor gets an isolated workspace.
"""

import uuid
from typing import Optional

import structlog
from fastapi import Header, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.document_chunk import DocumentChunk

logger = structlog.get_logger()


async def get_current_workspace(
    x_session_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """
    Resolve or provision an isolated Workspace for the current visitor session.
    If x_session_id is provided, maps to a unique User and Workspace.
    If not provided (e.g. scripts/CLI), falls back to the default workspace.
    """
    if x_session_id and x_session_id.strip():
        clean_sid = x_session_id.strip()[:64]
        email = f"session_{clean_sid}@ragforge.local"
        name = f"Session ({clean_sid[:8]})"
    else:
        email = "user@ragforge.dev"
        name = "Default Workspace"

    # 1. Find user
    result = await db.execute(select(User).where(User.email == email).limit(1))
    user = result.scalar_one_or_none()

    if not user:
        user = User(email=email, name=name)
        db.add(user)
        await db.flush()
        workspace = Workspace(user_id=user.id, name=name)
        db.add(workspace)
        await db.flush()

        # Seed sample demo knowledge base for instant portfolio readiness
        try:
            await _seed_sample_kb_for_workspace(workspace, db)
            await db.commit()
        except Exception as e:
            logger.warning("Failed to seed sample KB for new workspace", error=str(e))
            await db.commit()

        return workspace

    # 2. Find workspace for existing user
    result = await db.execute(
        select(Workspace).where(Workspace.user_id == user.id).limit(1)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        workspace = Workspace(user_id=user.id, name=name)
        db.add(workspace)
        await db.flush()
        try:
            await _seed_sample_kb_for_workspace(workspace, db)
            await db.commit()
        except Exception as e:
            logger.warning("Failed to seed sample KB for workspace", error=str(e))
            await db.commit()

    return workspace


async def _seed_sample_kb_for_workspace(workspace: Workspace, db: AsyncSession):
    """Seed an isolated Demo Knowledge Base for a new visitor workspace."""
    kb = KnowledgeBase(
        workspace_id=workspace.id,
        name="Demo Knowledge Base",
        description="Pre-seeded sample knowledge base with TechCorp FY2024 Annual Report for instant testing.",
    )
    db.add(kb)
    await db.flush()

    # Clone from an existing READY template document if available
    result = await db.execute(
        select(Document)
        .where(Document.filename == "techcorp_annual_report_2024.md", Document.status == "READY")
        .limit(1)
    )
    template_doc = result.scalar_one_or_none()

    if template_doc:
        new_doc_id = uuid.uuid4()
        new_doc = Document(
            id=new_doc_id,
            knowledge_base_id=kb.id,
            filename=template_doc.filename,
            file_type=template_doc.file_type,
            file_size=template_doc.file_size,
            status="READY",
            page_count=template_doc.page_count,
            chunk_count=template_doc.chunk_count,
            summary=template_doc.summary,
            topics=template_doc.topics,
            entities=template_doc.entities,
            suggested_questions=template_doc.suggested_questions,
            metadata_=template_doc.metadata_,
        )
        db.add(new_doc)
        await db.flush()

        # Clone document chunks
        chunks_res = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == template_doc.id)
            .order_by(DocumentChunk.chunk_index)
        )
        template_chunks = chunks_res.scalars().all()
        for tc in template_chunks:
            chunk = DocumentChunk(
                document_id=new_doc_id,
                chunk_index=tc.chunk_index,
                content=tc.content,
                page_number=tc.page_number,
                token_count=tc.token_count,
                embedding=tc.embedding,
                metadata_=tc.metadata_,
                search_vector=tc.search_vector,
            )
            db.add(chunk)
        await db.flush()
        logger.info(
            "Seeded demo KB for new workspace",
            workspace_id=str(workspace.id),
            kb_id=str(kb.id),
            chunks=len(template_chunks),
        )
