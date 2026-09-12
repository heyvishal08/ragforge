"""Query Log model — records every query for observability."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    query_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retrieval_strategy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retrieved_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reranked_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    vector_search_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    keyword_search_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    fusion_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    rerank_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    generation_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="query_logs")
