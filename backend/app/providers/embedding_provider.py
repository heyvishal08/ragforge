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


class FastEmbedProvider(EmbeddingProvider):
    """FastEmbed (ONNX Runtime) embedding provider — ultra-low memory (~30MB overhead) for 512MB RAM cloud containers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from fastembed import TextEmbedding
        
        # Normalize model name for fastembed
        normalized_name = model_name
        if "/" not in normalized_name:
            if "minilm" in normalized_name.lower():
                normalized_name = "sentence-transformers/all-MiniLM-L6-v2"
            elif "bge" in normalized_name.lower():
                normalized_name = "BAAI/bge-small-en-v1.5"
        
        logger.info("Loading FastEmbed ONNX embedding model", model=normalized_name)
        self.model_name = normalized_name
        self.model = TextEmbedding(model_name=normalized_name)
        self._dimension = 384
        logger.info("FastEmbed embedding model loaded", model=normalized_name, dimension=self._dimension)
    
    def embed(self, text: str) -> list[float]:
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = list(self.model.embed(texts, batch_size=16))
        return [e.tolist() for e in embeddings]
    
    @property
    def dimension(self) -> int:
        return self._dimension


class SentenceTransformerProvider(EmbeddingProvider):
    """Local sentence-transformers embedding provider optimized for local environments."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        import gc
        import torch
        # Cap PyTorch thread count to prevent multi-threaded memory bloat
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        torch.set_grad_enabled(False)
        
        from sentence_transformers import SentenceTransformer
        
        logger.info("Loading sentence-transformers model", model=model_name)
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
        provider_name = (settings.embedding_provider or "fastembed").lower()
        if provider_name in ("fastembed", "auto"):
            try:
                _embedding_provider = FastEmbedProvider(settings.embedding_model)
            except Exception as e:
                logger.warning("Failed to initialize FastEmbed; attempting sentence-transformers fallback", error=str(e))
                _embedding_provider = SentenceTransformerProvider(settings.embedding_model)
        elif provider_name == "sentence-transformer":
            try:
                _embedding_provider = SentenceTransformerProvider(settings.embedding_model)
            except Exception as e:
                logger.warning("Failed to initialize SentenceTransformer; falling back to FastEmbed", error=str(e))
                _embedding_provider = FastEmbedProvider(settings.embedding_model)
        else:
            try:
                _embedding_provider = FastEmbedProvider(settings.embedding_model)
            except Exception:
                _embedding_provider = SentenceTransformerProvider(settings.embedding_model)
    
    return _embedding_provider
