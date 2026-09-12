"""Tests for the query router."""

import pytest
from app.rag.query_router import QueryRouter


class TestQueryRouter:
    """Test query classification logic."""

    def setup_method(self):
        self.router = QueryRouter()

    def test_document_query(self):
        """Standard document questions classified as DOCUMENT_QUERY."""
        result = self.router.classify("What does the report say about AI?")
        assert result == "DOCUMENT_QUERY"

    def test_data_query_with_csv(self):
        """Numerical/analytical queries classified as DATA_QUERY when CSV present."""
        result = self.router.classify("What was the total revenue in Q3?", has_csv=True)
        assert result == "DATA_QUERY"

    def test_data_query_without_csv(self):
        """Numerical queries NOT classified as DATA_QUERY without CSV."""
        result = self.router.classify("What was the total revenue?", has_csv=False)
        assert result == "DOCUMENT_QUERY"

    def test_multi_document_query(self):
        """Comparison queries classified as MULTI_DOCUMENT_QUERY."""
        result = self.router.classify(
            "Compare the AI strategies between the two companies",
            document_count=3,
        )
        assert result == "MULTI_DOCUMENT_QUERY"

    def test_comparison_single_doc(self):
        """Comparison keywords don't trigger MULTI_DOCUMENT_QUERY with single doc."""
        result = self.router.classify(
            "Compare the results",
            document_count=1,
        )
        assert result == "DOCUMENT_QUERY"

    def test_general_query(self):
        """Simple questions default to DOCUMENT_QUERY."""
        result = self.router.classify("Tell me about machine learning")
        assert result == "DOCUMENT_QUERY"
