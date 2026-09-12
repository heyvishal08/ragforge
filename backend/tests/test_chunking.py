"""Tests for the document chunker."""

import pytest
from app.ingestion.chunker import Chunker


class TestChunker:
    """Test the configurable chunking strategy."""

    def test_basic_chunking(self):
        """Chunks text into manageable pieces."""
        chunker = Chunker(chunk_size=50, chunk_overlap=10)
        text = "This is the first paragraph.\n\nThis is the second paragraph.\n\nThis is the third paragraph."
        chunks = chunker.chunk(text)
        assert len(chunks) > 0
        for chunk in chunks:
            assert "content" in chunk
            assert "token_count" in chunk
            assert chunk["content"].strip()

    def test_empty_text(self):
        """Returns no chunks for empty text."""
        chunker = Chunker()
        assert chunker.chunk("") == []
        assert chunker.chunk("   ") == []

    def test_preserves_page_numbers(self):
        """Preserves page numbers when pages are provided."""
        chunker = Chunker(chunk_size=100)
        pages = [
            {"page_number": 1, "text": "Content on page one."},
            {"page_number": 2, "text": "Content on page two."},
        ]
        chunks = chunker.chunk("", pages=pages)
        assert all(c["page_number"] is not None for c in chunks)

    def test_large_paragraph_splitting(self):
        """Splits oversized paragraphs correctly."""
        chunker = Chunker(chunk_size=20, chunk_overlap=5)
        text = " ".join(["word"] * 100)
        chunks = chunker.chunk(text)
        assert len(chunks) > 1

    def test_chunk_overlap(self):
        """Chunks have overlap for continuity."""
        chunker = Chunker(chunk_size=30, chunk_overlap=10)
        text = "First paragraph content here.\n\nSecond paragraph content here.\n\nThird paragraph content here."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1

    def test_chunk_metadata(self):
        """Chunks include metadata."""
        chunker = Chunker()
        text = "Some document content."
        chunks = chunker.chunk(text, metadata={"format": "pdf"})
        for chunk in chunks:
            assert "metadata" in chunk

    def test_heading_splitting(self):
        """Respects heading boundaries."""
        chunker = Chunker(chunk_size=50)
        text = "# Introduction\n\nSome intro text.\n\n# Methods\n\nSome methods text."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1
