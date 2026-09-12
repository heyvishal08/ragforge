"""
Configurable document chunker — paragraph and heading-aware splitting.
"""

import re
from typing import Optional

import structlog

logger = structlog.get_logger()


class Chunker:
    """
    Configurable text chunker that respects document structure.
    
    Strategy:
    1. Split by page boundaries (if available)
    2. Within each page, split by headings/paragraphs
    3. Merge small paragraphs up to chunk_size
    4. Split oversized paragraphs with overlap
    """
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(
        self,
        text: str,
        pages: Optional[list] = None,
        metadata: Optional[dict] = None,
    ) -> list[dict]:
        """
        Split text into chunks with metadata.
        
        Returns list of:
            {
                "content": str,
                "page_number": int | None,
                "token_count": int,
                "metadata": dict,
            }
        """
        if pages:
            return self._chunk_with_pages(pages, metadata or {})
        else:
            return self._chunk_text(text, page_number=None, metadata=metadata or {})
    
    def _chunk_with_pages(self, pages: list, metadata: dict) -> list[dict]:
        """Chunk document page by page, preserving page numbers."""
        all_chunks = []
        for page in pages:
            page_chunks = self._chunk_text(
                page["text"],
                page_number=page.get("page_number"),
                metadata=metadata,
            )
            all_chunks.extend(page_chunks)
        return all_chunks
    
    def _chunk_text(
        self,
        text: str,
        page_number: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> list[dict]:
        """Split a text block into chunks respecting paragraph boundaries."""
        if not text.strip():
            return []
        
        # Split into paragraphs (double newlines or heading patterns)
        paragraphs = self._split_into_paragraphs(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = self._estimate_tokens(para)
            
            # If a single paragraph exceeds chunk_size, split it
            if para_length > self.chunk_size:
                # Flush current chunk first
                if current_chunk:
                    chunks.append(self._make_chunk(
                        "\n\n".join(current_chunk),
                        page_number,
                        metadata,
                    ))
                    current_chunk = []
                    current_length = 0
                
                # Split oversized paragraph with overlap
                sub_chunks = self._split_large_text(para)
                for sc in sub_chunks:
                    chunks.append(self._make_chunk(sc, page_number, metadata))
                continue
            
            # If adding this paragraph exceeds chunk_size, flush
            if current_length + para_length > self.chunk_size and current_chunk:
                chunks.append(self._make_chunk(
                    "\n\n".join(current_chunk),
                    page_number,
                    metadata,
                ))
                
                # Keep overlap from end of previous chunk
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-1]
                    if self._estimate_tokens(overlap_text) <= self.chunk_overlap:
                        current_chunk = [overlap_text]
                        current_length = self._estimate_tokens(overlap_text)
                    else:
                        current_chunk = []
                        current_length = 0
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(para)
            current_length += para_length
        
        # Flush remaining
        if current_chunk:
            chunks.append(self._make_chunk(
                "\n\n".join(current_chunk),
                page_number,
                metadata,
            ))
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> list[str]:
        """Split text by paragraph boundaries and headings."""
        # Split on double newlines, or lines that look like headings
        parts = re.split(r'\n\s*\n|\n(?=[A-Z][A-Z\s]{2,}:?\n)|(?<=\n)(?=#{1,6}\s)', text)
        return [p.strip() for p in parts if p.strip()]
    
    def _split_large_text(self, text: str) -> list[str]:
        """Split an oversized text block into chunks with word-boundary overlap."""
        words = text.split()
        chunks = []
        
        # Approximate tokens per word ≈ 1.3
        words_per_chunk = int(self.chunk_size / 1.3)
        overlap_words = int(self.chunk_overlap / 1.3)
        
        start = 0
        while start < len(words):
            end = start + words_per_chunk
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            start = end - overlap_words if overlap_words > 0 else end
        
        return chunks
    
    def _make_chunk(self, content: str, page_number: Optional[int], metadata: dict) -> dict:
        """Create a chunk dict with metadata."""
        return {
            "content": content,
            "page_number": page_number,
            "token_count": self._estimate_tokens(content),
            "metadata": {**metadata, "page_number": page_number},
        }
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: ~1.3 tokens per word)."""
        return int(len(text.split()) * 1.3)
