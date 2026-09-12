"""
Hybrid retrieval — combines vector search and keyword search with Reciprocal Rank Fusion.
"""

import time
import uuid
from typing import Optional

import structlog
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.models.document import Document
from app.providers.embedding_provider import EmbeddingProvider

logger = structlog.get_logger()


class HybridRetriever:
    """
    Implements hybrid retrieval:
    1. Vector search (pgvector cosine similarity)
    2. Keyword search (PostgreSQL tsvector)
    3. Reciprocal Rank Fusion (RRF) to merge results
    """
    
    def __init__(self, db: AsyncSession, embedding_provider: EmbeddingProvider):
        self.db = db
        self.embedding_provider = embedding_provider
    
    async def search(
        self,
        query: str,
        knowledge_base_id: uuid.UUID,
        strategy: str = "hybrid",
        top_k: int = 20,
        document_ids: Optional[list[uuid.UUID]] = None,
    ) -> list[dict]:
        """
        Run retrieval with the specified strategy.
        Returns list of result dicts with scores and metadata.
        """
        if strategy == "vector":
            return await self._vector_search(query, knowledge_base_id, top_k, document_ids)
        elif strategy == "keyword":
            return await self._keyword_search(query, knowledge_base_id, top_k, document_ids)
        elif strategy == "hybrid":
            return await self._hybrid_search(query, knowledge_base_id, top_k, document_ids)
        else:
            raise ValueError(f"Unknown retrieval strategy: {strategy}")
    
    async def _vector_search(
        self,
        query: str,
        knowledge_base_id: uuid.UUID,
        top_k: int,
        document_ids: Optional[list[uuid.UUID]] = None,
    ) -> list[dict]:
        """Cosine similarity search."""
        query_embedding = self.embedding_provider.embed(query)
        
        doc_filter = ""
        params = {
            "kb_id": str(knowledge_base_id),
        }
        
        if document_ids:
            doc_ids_str = ",".join([f"'{str(did)}'" for did in document_ids])
            doc_filter = f"AND d.id IN ({doc_ids_str})"
        
        sql = text(f"""
            SELECT 
                c.id, c.content, c.page_number, c.chunk_index, c.token_count,
                d.filename,
                c.embedding
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE d.knowledge_base_id = :kb_id
            AND c.embedding IS NOT NULL
            {doc_filter}
        """)
        
        result = await self.db.execute(sql, params)
        rows = result.fetchall()
        
        import numpy as np
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            q_norm = 1e-9
            
        scored = []
        for row in rows:
            emb = row[6]
            if emb:
                c_vec = np.array(emb, dtype=np.float32)
                c_norm = np.linalg.norm(c_vec)
                if c_norm > 0:
                    sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
                else:
                    sim = 0.0
            else:
                sim = 0.0
                
            scored.append({
                "chunk_id": row[0],
                "content": row[1],
                "page_number": row[2],
                "chunk_index": row[3],
                "token_count": row[4],
                "document_name": row[5],
                "score": sim,
                "retrieval_method": "vector",
            })
            
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
    
    async def _keyword_search(
        self,
        query: str,
        knowledge_base_id: uuid.UUID,
        top_k: int,
        document_ids: Optional[list[uuid.UUID]] = None,
    ) -> list[dict]:
        """Full-text search using PostgreSQL tsvector."""
        doc_filter = ""
        params = {
            "kb_id": str(knowledge_base_id),
            "query": query,
            "top_k": top_k,
        }
        
        if document_ids:
            doc_ids_str = ",".join([f"'{str(did)}'" for did in document_ids])
            doc_filter = f"AND d.id IN ({doc_ids_str})"
        
        sql = text(f"""
            SELECT 
                c.id, c.content, c.page_number, c.chunk_index, c.token_count,
                d.filename,
                ts_rank(c.search_vector, plainto_tsquery('english', :query)) as rank
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE d.knowledge_base_id = :kb_id
            AND c.search_vector @@ plainto_tsquery('english', :query)
            {doc_filter}
            ORDER BY rank DESC
            LIMIT :top_k
        """)
        
        result = await self.db.execute(sql, params)
        rows = result.fetchall()
        
        return [
            {
                "chunk_id": row[0],
                "content": row[1],
                "page_number": row[2],
                "chunk_index": row[3],
                "token_count": row[4],
                "document_name": row[5],
                "score": float(row[6]) if row[6] else 0,
                "retrieval_method": "keyword",
            }
            for row in rows
        ]
    
    async def _hybrid_search(
        self,
        query: str,
        knowledge_base_id: uuid.UUID,
        top_k: int,
        document_ids: Optional[list[uuid.UUID]] = None,
    ) -> list[dict]:
        """
        Run both vector and keyword search, then fuse with Reciprocal Rank Fusion.
        """
        vector_results = await self._vector_search(query, knowledge_base_id, top_k, document_ids)
        keyword_results = await self._keyword_search(query, knowledge_base_id, top_k, document_ids)
        
        return self._reciprocal_rank_fusion(vector_results, keyword_results, top_k)
    
    def _reciprocal_rank_fusion(
        self,
        vector_results: list[dict],
        keyword_results: list[dict],
        top_k: int,
        k: int = 60,
    ) -> list[dict]:
        """
        Reciprocal Rank Fusion (RRF) — merges ranked lists.
        
        RRF_score(d) = Σ 1/(k + rank(d)) for each result list
        
        k=60 is the standard constant from the original RRF paper.
        """
        scores = {}
        result_map = {}
        
        for rank, result in enumerate(vector_results):
            chunk_id = str(result["chunk_id"])
            rrf_score = 1.0 / (k + rank + 1)
            scores[chunk_id] = scores.get(chunk_id, 0) + rrf_score
            result_map[chunk_id] = result
        
        for rank, result in enumerate(keyword_results):
            chunk_id = str(result["chunk_id"])
            rrf_score = 1.0 / (k + rank + 1)
            scores[chunk_id] = scores.get(chunk_id, 0) + rrf_score
            if chunk_id not in result_map:
                result_map[chunk_id] = result
            else:
                # Mark as found by both methods
                result_map[chunk_id]["retrieval_method"] = "hybrid"
        
        # Sort by RRF score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for chunk_id, rrf_score in ranked[:top_k]:
            result = result_map[chunk_id].copy()
            result["score"] = rrf_score
            result["retrieval_method"] = result.get("retrieval_method", "hybrid")
            results.append(result)
        
        return results
