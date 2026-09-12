"""
SQLAlchemy ORM models for RAGForge.

All models are imported here so Base.metadata.create_all() discovers them.
"""

from app.models.user import User
from app.models.workspace import Workspace
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.citation import Citation
from app.models.query_log import QueryLog
from app.models.evaluation import EvaluationRun, EvaluationQuestion

__all__ = [
    "User",
    "Workspace",
    "KnowledgeBase",
    "Document",
    "DocumentChunk",
    "Conversation",
    "Message",
    "Citation",
    "QueryLog",
    "EvaluationRun",
    "EvaluationQuestion",
]
