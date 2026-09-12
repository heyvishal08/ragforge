"""Tests for the Reciprocal Rank Fusion implementation."""

import pytest
from app.rag.retrieval.hybrid import HybridRetriever


class TestReciprocalRankFusion:
    """Test the RRF merge algorithm."""

    def test_basic_fusion(self):
        """Two result lists are correctly merged."""
        retriever = HybridRetriever.__new__(HybridRetriever)
        
        vector_results = [
            {"chunk_id": "a", "content": "chunk A", "score": 0.9, "retrieval_method": "vector", "document_name": "doc1"},
            {"chunk_id": "b", "content": "chunk B", "score": 0.8, "retrieval_method": "vector", "document_name": "doc1"},
            {"chunk_id": "c", "content": "chunk C", "score": 0.7, "retrieval_method": "vector", "document_name": "doc2"},
        ]
        keyword_results = [
            {"chunk_id": "b", "content": "chunk B", "score": 0.9, "retrieval_method": "keyword", "document_name": "doc1"},
            {"chunk_id": "d", "content": "chunk D", "score": 0.8, "retrieval_method": "keyword", "document_name": "doc2"},
            {"chunk_id": "a", "content": "chunk A", "score": 0.7, "retrieval_method": "keyword", "document_name": "doc1"},
        ]
        
        results = retriever._reciprocal_rank_fusion(vector_results, keyword_results, top_k=5)
        
        assert len(results) > 0
        # Chunks appearing in both lists should be ranked higher
        chunk_ids = [r["chunk_id"] for r in results]
        # "b" and "a" appear in both lists, so they should be near the top
        assert "b" in chunk_ids[:2] or "a" in chunk_ids[:2]

    def test_empty_lists(self):
        """Handles empty result lists gracefully."""
        retriever = HybridRetriever.__new__(HybridRetriever)
        results = retriever._reciprocal_rank_fusion([], [], top_k=5)
        assert results == []

    def test_single_list(self):
        """Works with one empty list."""
        retriever = HybridRetriever.__new__(HybridRetriever)
        vector_results = [
            {"chunk_id": "a", "content": "chunk A", "score": 0.9, "retrieval_method": "vector", "document_name": "doc1"},
        ]
        results = retriever._reciprocal_rank_fusion(vector_results, [], top_k=5)
        assert len(results) == 1

    def test_top_k_limiting(self):
        """Respects the top_k limit."""
        retriever = HybridRetriever.__new__(HybridRetriever)
        vector_results = [
            {"chunk_id": str(i), "content": f"chunk {i}", "score": 0.9 - i*0.01, "retrieval_method": "vector", "document_name": "doc1"}
            for i in range(10)
        ]
        results = retriever._reciprocal_rank_fusion(vector_results, [], top_k=3)
        assert len(results) == 3

    def test_hybrid_method_labeling(self):
        """Chunks found by both methods are labeled as 'hybrid'."""
        retriever = HybridRetriever.__new__(HybridRetriever)
        shared = {"chunk_id": "x", "content": "shared chunk", "score": 0.9, "retrieval_method": "vector", "document_name": "doc1"}
        vector_results = [shared.copy()]
        keyword_results = [{**shared, "retrieval_method": "keyword"}]
        results = retriever._reciprocal_rank_fusion(vector_results, keyword_results, top_k=5)
        assert results[0]["retrieval_method"] == "hybrid"
