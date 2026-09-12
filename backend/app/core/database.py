"""
Async SQLAlchemy engine, session factory, and database utilities.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Asyncpg expects ?ssl=require rather than ?sslmode=require
db_url = settings.database_url
if "sslmode=" in db_url:
    db_url = db_url.replace("sslmode=require", "ssl=require").replace("sslmode=prefer", "ssl=prefer")

engine = create_async_engine(
    db_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def run_migrations():
    """Create all tables on startup (dev convenience). Use Alembic in production."""
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        except Exception:
            pass
        # Import all models so they are registered with Base.metadata
        import app.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

