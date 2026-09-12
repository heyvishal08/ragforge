"""Knowledge Base model."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="knowledge_bases")
    documents = relationship(
        "Document", back_populates="knowledge_base", cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation", back_populates="knowledge_base", cascade="all, delete-orphan"
    )
    evaluation_runs = relationship(
        "EvaluationRun", back_populates="knowledge_base", cascade="all, delete-orphan"
    )
    query_logs = relationship(
        "QueryLog", back_populates="knowledge_base", cascade="all, delete-orphan"
    )
