"""
Application configuration loaded from environment variables.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration for RAGForge backend."""

    # ─── Database ───
    database_url: str = "postgresql+asyncpg://ragforge:ragforge@localhost:5432/ragforge"
    database_url_sync: str = "postgresql://ragforge:ragforge@localhost:5432/ragforge"

    # ─── Groq ───
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"

    # ─── Embedding ───
    embedding_provider: str = "fastembed"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # ─── Reranker ───
    reranker_provider: str = "none"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ─── Application ───
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # ─── Ingestion ───
    max_file_size_mb: int = 50
    chunk_size: int = 512
    chunk_overlap: int = 50

    # ─── Retrieval ───
    vector_search_top_k: int = 20
    keyword_search_top_k: int = 20
    rerank_top_k: int = 8
    min_evidence_threshold: float = 0.3

    # ─── Security ───
    cors_origins: List[str] = ["http://localhost:3000"]
    rate_limit_per_minute: int = 60

    # ─── Paths ───
    upload_dir: str = "data/uploads"
    demo_dir: str = "data/demo"

    model_config = {
        "env_file": [".env", "../.env"],
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
