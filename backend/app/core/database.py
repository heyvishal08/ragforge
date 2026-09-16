"""
Async SQLAlchemy engine, session factory, and database utilities.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

from sqlalchemy.engine.url import make_url

def normalize_asyncpg_url(raw_url: str) -> str:
    """Normalize database URL for asyncpg by stripping unsupported query parameters like channel_binding."""
    try:
        url = make_url(raw_url)
        supported_params = {
            "ssl", "timeout", "command_timeout", "statement_cache_size",
            "max_cached_statement_lifetime", "max_cacheable_statement_size",
            "server_settings", "target_session_attrs"
        }
        query = dict(url.query)
        if "sslmode" in query:
            val = query.pop("sslmode")
            if val in ("require", "verify-ca", "verify-full"):
                query["ssl"] = "require"
            elif val == "prefer":
                query["ssl"] = "prefer"
        filtered_query = {k: v for k, v in query.items() if k in supported_params}
        if "localhost" not in (url.host or "") and "127.0.0.1" not in (url.host or "") and "ssl" not in filtered_query:
            filtered_query["ssl"] = "require"
        return url._replace(query=filtered_query).render_as_string(hide_password=False)
    except Exception:
        return raw_url

db_url = normalize_asyncpg_url(settings.database_url)

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
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    except Exception:
        pass

    async with engine.begin() as conn:
        # Import all models so they are registered with Base.metadata
        import app.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

