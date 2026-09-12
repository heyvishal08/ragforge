"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ─── Knowledge Base Schemas ───

class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Document Schemas ───

class DocumentResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    page_count: Optional[int]
    chunk_count: Optional[int]
    summary: Optional[str]
    topics: Optional[list]
    entities: Optional[list]
    suggested_questions: Optional[list]
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DocumentChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    content: str
    page_number: Optional[int]
    token_count: Optional[int]
    metadata: Optional[dict] = Field(None, alias="metadata_")

    model_config = {"from_attributes": True, "populate_by_name": True}


# ─── Chat Schemas ───

class ChatRequest(BaseModel):
    knowledge_base_id: UUID
    conversation_id: Optional[UUID] = None
    query: str = Field(..., min_length=1, max_length=5000)
    retrieval_strategy: str = "hybrid"  # vector | keyword | hybrid
    document_ids: Optional[list[UUID]] = None


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    content: str
    citations: list["CitationResponse"]
    retrieval_metadata: Optional[dict]
    confidence: Optional[dict]

    model_config = {"from_attributes": True}


class CitationResponse(BaseModel):
    id: UUID
    citation_index: int
    document_name: str
    page_number: Optional[int]
    chunk_content: str
    relevance_score: Optional[float]
    rerank_score: Optional[float]
    retrieval_method: Optional[str]

    model_config = {"from_attributes": True}


# ─── Conversation Schemas ───

class ConversationResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    citations: list[CitationResponse] = []
    retrieval_metadata: Optional[dict]
    latency_ms: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Retrieval Schemas ───

class RetrievalRequest(BaseModel):
    knowledge_base_id: UUID
    query: str = Field(..., min_length=1, max_length=5000)
    strategy: str = "hybrid"  # vector | keyword | hybrid
    top_k: int = Field(20, ge=1, le=100)
    rerank: bool = True
    document_ids: Optional[list[UUID]] = None


class RetrievalResult(BaseModel):
    chunk_id: UUID
    document_name: str
    page_number: Optional[int]
    content: str
    score: float
    retrieval_method: str
    rerank_score: Optional[float] = None


class RetrievalResponse(BaseModel):
    results: list[RetrievalResult]
    metadata: dict


# ─── Evaluation Schemas ───

class EvaluationRunCreate(BaseModel):
    knowledge_base_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    questions: list["EvaluationQuestionInput"]


class EvaluationQuestionInput(BaseModel):
    question: str
    expected_answer: Optional[str] = None
    expected_sources: Optional[list[str]] = None


class EvaluationRunResponse(BaseModel):
    id: UUID
    name: str
    status: str
    total_questions: Optional[int]
    faithfulness: Optional[float]
    answer_relevance: Optional[float]
    context_precision: Optional[float]
    context_recall: Optional[float]
    retrieval_success_rate: Optional[float]
    hallucination_rate: Optional[float]
    avg_latency_ms: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── Analytics Schemas ───

class QueryLogResponse(BaseModel):
    id: UUID
    query: str
    query_type: Optional[str]
    retrieval_strategy: Optional[str]
    retrieved_count: Optional[int]
    reranked_count: Optional[int]
    final_count: Optional[int]
    embedding_latency_ms: Optional[float]
    vector_search_latency_ms: Optional[float]
    keyword_search_latency_ms: Optional[float]
    fusion_latency_ms: Optional[float]
    rerank_latency_ms: Optional[float]
    generation_latency_ms: Optional[float]
    total_latency_ms: Optional[float]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    model: Optional[str]
    success: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsSummary(BaseModel):
    total_queries: int
    avg_latency_ms: float
    success_rate: float
    total_documents: int
    total_chunks: int
    total_knowledge_bases: int
    recent_queries: list[QueryLogResponse]
