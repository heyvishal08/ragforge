"""
Reranker — cross-encoder reranking for precision-focused retrieval.
"""

from abc import ABC, abstractmethod

import structlog

from app.core.config import settings

logger = structlog.get_logger()

_reranker = None


class Reranker(ABC):
    """Abstract reranker interface."""
    
    @abstractmethod
    async def rerank(self, query: str, results: list[dict], top_k: int = None) -> list[dict]:
        """Rerank retrieval results and return top-K."""
        ...


class CrossEncoderReranker(Reranker):
    """Cross-encoder reranker using sentence-transformers."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        from sentence_transformers import CrossEncoder
        
        logger.info("Loading reranker model", model=model_name)
        self.model = CrossEncoder(model_name)
        self.default_top_k = settings.rerank_top_k
        logger.info("Reranker model loaded", model=model_name)
    
    async def rerank(self, query: str, results: list[dict], top_k: int = None) -> list[dict]:
        """
        Rerank candidates using a cross-encoder.
        
        Takes the broader candidate set and returns the most relevant chunks.
        """
        if not results:
            return results
        
        top_k = top_k or self.default_top_k
        
        # Create query-document pairs for the cross-encoder
        pairs = [(query, r["content"]) for r in results]
        
        # Score all pairs
        scores = self.model.predict(pairs)
        
        # Attach rerank scores
        for result, score in zip(results, scores):
            result["rerank_score"] = float(score)
        
        # Sort by rerank score and take top-K
        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        
        return results[:top_k]


class NoOpReranker(Reranker):
    """Pass-through reranker that preserves Hybrid Search RRF scores without loading heavy CrossEncoder."""
    
    async def rerank(self, query: str, results: list[dict], top_k: int = None) -> list[dict]:
        top_k = top_k or settings.rerank_top_k
        for r in results:
            if "rerank_score" not in r:
                r["rerank_score"] = float(r.get("score", 0.0))
        return results[:top_k]


def get_reranker() -> Reranker:
    """Factory — returns a configured reranker (singleton)."""
    global _reranker
    
    if _reranker is None:
        if settings.reranker_provider == "cross-encoder":
            _reranker = CrossEncoderReranker(settings.reranker_model)
        elif settings.reranker_provider == "none":
            _reranker = NoOpReranker()
        else:
            raise ValueError(f"Unknown reranker provider: {settings.reranker_provider}")
    
    return _reranker
