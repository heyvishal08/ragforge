"""
Embedding provider abstraction — configurable embedding backend.
"""

from abc import ABC, abstractmethod
from typing import Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Singleton cache
_embedding_provider = None


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Embed a single text."""
        ...
    
    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        ...
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        ...


class SentenceTransformerProvider(EmbeddingProvider):
    """Local sentence-transformers embedding provider."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        
        logger.info("Loading embedding model", model=model_name)
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
        logger.info("Embedding model loaded", model=model_name, dimension=self._dimension)
    
    def embed(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True, batch_size=32)
        return embeddings.tolist()
    
    @property
    def dimension(self) -> int:
        return self._dimension


def get_embedding_provider() -> EmbeddingProvider:
    """Factory — returns a configured embedding provider (singleton)."""
    global _embedding_provider
    
    if _embedding_provider is None:
        if settings.embedding_provider == "sentence-transformer":
            _embedding_provider = SentenceTransformerProvider(settings.embedding_model)
        else:
            raise ValueError(f"Unknown embedding provider: {settings.embedding_provider}")
    
    return _embedding_provider
