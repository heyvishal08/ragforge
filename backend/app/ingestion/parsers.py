"""
Document parsers — extract text and metadata from various file formats.
"""

import os
from typing import Optional

import structlog

logger = structlog.get_logger()


def parse_document(file_path: str, file_type: str) -> dict:
    """
    Parse a document and return extracted content.
    
    Returns:
        {
            "text": str,           # Full extracted text
            "pages": list[dict],   # Per-page content (if applicable)
            "page_count": int,
            "metadata": dict,
        }
    """
    parsers = {
        "pdf": parse_pdf,
        "docx": parse_docx,
        "txt": parse_text,
        "md": parse_text,
        "csv": parse_csv,
    }
    
    parser = parsers.get(file_type)
    if not parser:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    return parser(file_path)


def parse_pdf(file_path: str) -> dict:
    """Parse PDF using PyMuPDF, preserving page numbers."""
    import fitz  # PyMuPDF
    
    doc = fitz.open(file_path)
    pages = []
    full_text_parts = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages.append({
                "page_number": page_num + 1,
                "text": text,
            })
            full_text_parts.append(text)
    
    doc.close()
    
    return {
        "text": "\n\n".join(full_text_parts),
        "pages": pages,
        "page_count": len(pages),
        "metadata": {"format": "pdf"},
    }


def parse_docx(file_path: str) -> dict:
    """Parse DOCX using python-docx."""
    from docx import Document
    
    doc = Document(file_path)
    paragraphs = []
    
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append({
                "text": para.text,
                "style": para.style.name if para.style else None,
            })
    
    full_text = "\n\n".join([p["text"] for p in paragraphs])
    
    return {
        "text": full_text,
        "pages": [{"page_number": 1, "text": full_text}],
        "page_count": 1,
        "metadata": {
            "format": "docx",
            "paragraph_count": len(paragraphs),
        },
    }


def parse_text(file_path: str) -> dict:
    """Parse plain text or markdown files."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    
    return {
        "text": text,
        "pages": [{"page_number": 1, "text": text}],
        "page_count": 1,
        "metadata": {"format": os.path.splitext(file_path)[1].lstrip(".")},
    }


def parse_csv(file_path: str) -> dict:
    """
    Parse CSV file — extract both textual representation and structured metadata.
    Does NOT treat each row as plain text; preserves schema information.
    """
    import pandas as pd
    
    df = pd.read_csv(file_path)
    
    # Build a rich textual representation
    schema_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        nunique = df[col].nunique()
        sample = str(df[col].dropna().iloc[0]) if len(df[col].dropna()) > 0 else "N/A"
        schema_info.append(f"- {col} ({dtype}): {nunique} unique values, sample: {sample}")
    
    schema_text = "SCHEMA:\n" + "\n".join(schema_info)
    
    # Create a statistical summary
    stats_text = "STATISTICS:\n" + df.describe(include="all").to_string()
    
    # Create row samples (first and last few rows)
    sample_text = "SAMPLE DATA (first 10 rows):\n" + df.head(10).to_string()
    
    full_text = f"{schema_text}\n\n{stats_text}\n\n{sample_text}"
    
    # Also store raw data path for the CSV analyzer
    metadata = {
        "format": "csv",
        "columns": list(df.columns),
        "row_count": len(df),
        "column_count": len(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }
    
    return {
        "text": full_text,
        "pages": [{"page_number": 1, "text": full_text}],
        "page_count": 1,
        "metadata": metadata,
    }
