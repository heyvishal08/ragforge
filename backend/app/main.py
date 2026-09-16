"""
RAGForge Backend — Evidence-first AI Knowledge Engine

FastAPI application entry point.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, run_migrations
from app.api import documents, knowledge_bases, chat, retrieval, evaluations, analytics

logger = structlog.get_logger()


import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Starting RAGForge backend", version="0.1.0")
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs("data/temp", exist_ok=True)
    await run_migrations()
    yield
    await engine.dispose()
    logger.info("RAGForge backend shut down")


app = FastAPI(
    title="RAGForge",
    description="Evidence-first AI knowledge engine — API",
    version="0.1.0",
    lifespan=lifespan,
)

# ─── CORS ───
cors_kwargs = {
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "allow_origin_regex": r"https://.*\.vercel\.app",
}
if "*" in settings.cors_origins:
    cors_kwargs["allow_origins"] = ["*"]
    cors_kwargs["allow_credentials"] = False
else:
    cors_kwargs["allow_origins"] = settings.cors_origins
    cors_kwargs["allow_credentials"] = True

app.add_middleware(CORSMiddleware, **cors_kwargs)

# ─── Routers ───
app.include_router(knowledge_bases.router, prefix="/api/knowledge-bases", tags=["Knowledge Bases"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(retrieval.router, prefix="/api/retrieval", tags=["Retrieval"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["Evaluations"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ragforge"}


# ─── Static Frontend (Next.js Export) ───
frontend_dirs = [
    Path(__file__).resolve().parents[2] / "frontend" / "out",
    Path("frontend/out"),
    Path("out"),
]
for f_dir in frontend_dirs:
    if f_dir.exists():
        app.mount("/", StaticFiles(directory=str(f_dir), html=True), name="frontend")
        break

