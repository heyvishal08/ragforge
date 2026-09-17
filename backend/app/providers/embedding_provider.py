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
    """Local sentence-transformers embedding provider optimized for 512MB RAM cloud containers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        import gc
        import torch
        # Cap PyTorch thread count to prevent multi-threaded memory bloat on 512MB RAM
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        torch.set_grad_enabled(False)
        
        from sentence_transformers import SentenceTransformer
        
        logger.info("Loading embedding model", model=model_name)
        self.model = SentenceTransformer(model_name)
        self.model.eval()
        self._dimension = self.model.get_sentence_embedding_dimension()
        gc.collect()
        logger.info("Embedding model loaded", model=model_name, dimension=self._dimension)
    
    def embed(self, text: str) -> list[float]:
        import torch
        with torch.no_grad():
            embedding = self.model.encode(text, normalize_embeddings=True, show_progress_bar=False)
        return embedding.tolist()
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        import gc
        import torch
        with torch.no_grad():
            embeddings = self.model.encode(
                texts, normalize_embeddings=True, batch_size=16, show_progress_bar=False
            )
        gc.collect()
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
