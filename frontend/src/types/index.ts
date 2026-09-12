export interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  knowledge_base_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  page_count: number | null;
  chunk_count: number | null;
  summary: string | null;
  topics: string[] | null;
  entities: string[] | null;
  suggested_questions: string[] | null;
  error_message: string | null;
  created_at: string;
  processed_at: string | null;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
  page_number: number | null;
  token_count: number | null;
  metadata: Record<string, unknown> | null;
}

export interface Citation {
  id: string;
  citation_index: number;
  document_name: string;
  page_number: number | null;
  chunk_content: string;
  relevance_score: number | null;
  rerank_score: number | null;
  retrieval_method: string | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  retrieval_metadata: RetrievalMetadata | null;
  latency_ms: number | null;
  created_at: string;
}

export interface RetrievalMetadata {
  query_type: string;
  retrieval_strategy: string;
  retrieved_candidates: number;
  reranked_candidates: number;
  final_evidence_count: number;
  timings: {
    retrieval_ms: number;
    rerank_ms: number;
    generation_ms: number;
    total_ms: number;
  };
  insufficient_evidence?: boolean;
}

export interface Conversation {
  id: string;
  knowledge_base_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Confidence {
  evidence_confidence: number;
  evidence_quality: number;
  retrieval_coverage: number;
}

export interface RetrievalResult {
  chunk_id: string;
  document_name: string;
  page_number: number | null;
  content: string;
  score: number;
  retrieval_method: string;
  rerank_score: number | null;
}

export interface RetrievalResponse {
  results: RetrievalResult[];
  metadata: Record<string, unknown>;
}

export interface EvaluationRun {
  id: string;
  name: string;
  status: string;
  total_questions: number | null;
  faithfulness: number | null;
  answer_relevance: number | null;
  context_precision: number | null;
  context_recall: number | null;
  retrieval_success_rate: number | null;
  hallucination_rate: number | null;
  avg_latency_ms: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface QueryLog {
  id: string;
  query: string;
  query_type: string | null;
  retrieval_strategy: string | null;
  retrieved_count: number | null;
  reranked_count: number | null;
  final_count: number | null;
  embedding_latency_ms: number | null;
  vector_search_latency_ms: number | null;
  keyword_search_latency_ms: number | null;
  fusion_latency_ms: number | null;
  rerank_latency_ms: number | null;
  generation_latency_ms: number | null;
  total_latency_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  model: string | null;
  success: boolean;
  created_at: string;
}

export interface AnalyticsSummary {
  total_queries: number;
  avg_latency_ms: number;
  success_rate: number;
  total_documents: number;
  total_chunks: number;
  total_knowledge_bases: number;
  recent_queries: QueryLog[];
}
