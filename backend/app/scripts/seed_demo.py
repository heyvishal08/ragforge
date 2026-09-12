"""
Seed script to populate a rich demo Knowledge Base with sample documents.
Can be run via: python -m app.scripts.seed_demo
"""

import asyncio
import os
import shutil
import uuid
import structlog
from sqlalchemy import select

from app.core.database import async_session, engine, run_migrations
from app.models.user import User
from app.models.workspace import Workspace
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.ingestion.pipeline import IngestionPipeline

logger = structlog.get_logger()

DEMO_FILES = [
    {
        "filename": "techcorp_annual_report_2024.md",
        "file_type": "md",
        "path": "data/demo/techcorp_annual_report_2024.md",
    },
    {
        "filename": "ai_research_trends_2024.md",
        "file_type": "md",
        "path": "data/demo/ai_research_trends_2024.md",
    },
    {
        "filename": "techcorp_sales_data_2024.csv",
        "file_type": "csv",
        "path": "data/demo/techcorp_sales_data_2024.csv",
    },
]


async def seed_demo():
    """Seed demo knowledge base and documents."""
    logger.info("Initializing database schema...")
    await run_migrations()

    async with async_session() as db:
        # Check or create default user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            user = User(email="demo@ragforge.dev", name="Lead AI Researcher")
            db.add(user)
            await db.flush()

        # Check or create workspace
        result = await db.execute(
            select(Workspace).where(Workspace.user_id == user.id).limit(1)
        )
        workspace = result.scalar_one_or_none()
        if not workspace:
            workspace = Workspace(user_id=user.id, name="Research & Intelligence")
            db.add(workspace)
            await db.flush()

        # Check or create demo Knowledge Base
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.workspace_id == workspace.id,
                KnowledgeBase.name == "Enterprise Intelligence Demo",
            ).limit(1)
        )
        kb = result.scalar_one_or_none()
        if not kb:
            kb = KnowledgeBase(
                workspace_id=workspace.id,
                name="Enterprise Intelligence Demo",
                description="Demo knowledge base containing TechCorp FY2024 financials, AI research trends, and regional sales metrics.",
            )
            db.add(kb)
            await db.flush()
            logger.info("Created Demo Knowledge Base", kb_id=str(kb.id))

        kb_id = kb.id
        await db.commit()

    # Process and ingest demo files
    for item in DEMO_FILES:
        rel_path = item["path"]
        if not os.path.exists(rel_path):
            parent_rel = os.path.join("..", rel_path)
            if os.path.exists(parent_rel):
                rel_path = parent_rel
            else:
                logger.warning("Demo file not found, skipping", path=rel_path)
                continue

        async with async_session() as db:
            # Check if document already exists
            result = await db.execute(
                select(Document).where(
                    Document.knowledge_base_id == kb_id,
                    Document.filename == item["filename"],
                ).limit(1)
            )
            existing_doc = result.scalar_one_or_none()
            if existing_doc and existing_doc.status == "READY":
                logger.info("Demo document already indexed", filename=item["filename"])
                continue

            file_size = os.path.getsize(rel_path)
            base_upload = "data" if os.path.exists("data") else os.path.join("..", "data")
            upload_dir = os.path.join(base_upload, "uploads", str(kb_id))
            os.makedirs(upload_dir, exist_ok=True)
            doc_id = uuid.uuid4()
            dest_path = os.path.join(upload_dir, f"{doc_id}.{item['file_type']}")
            shutil.copyfile(rel_path, dest_path)

            doc = Document(
                id=doc_id,
                knowledge_base_id=kb_id,
                filename=item["filename"],
                file_type=item["file_type"],
                file_size=file_size,
                status="UPLOADING",
                metadata_={"file_path": dest_path},
            )
            db.add(doc)
            await db.commit()

            logger.info("Starting ingestion for demo file", filename=item["filename"], doc_id=str(doc_id))
            pipeline = IngestionPipeline(db)
            try:
                await pipeline.process(str(doc_id), dest_path)
                await db.commit()
                logger.info("Successfully ingested demo file", filename=item["filename"])
            except Exception as e:
                logger.error("Failed to ingest demo file", filename=item["filename"], error=str(e))

    logger.info("Demo seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_demo())
