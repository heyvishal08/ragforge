"""
Tests for embedding provider.
"""

import pytest
from app.providers.embedding_provider import get_embedding_provider, FastEmbedProvider


def test_fastembed_provider():
    provider = get_embedding_provider()
    assert provider.dimension == 384
    
    # Test single embed
    vector = provider.embed("RAGForge evidence-based retrieval")
    assert isinstance(vector, list)
    assert len(vector) == 384
    assert all(isinstance(x, float) for x in vector)
    
    # Test batch embed
    batch = provider.embed_batch(["Query one", "Query two"])
    assert len(batch) == 2
    assert len(batch[0]) == 384
    assert len(batch[1]) == 384
