"""
Query Router — classifies user queries into processing types.
"""

import structlog

logger = structlog.get_logger()


class QueryRouter:
    """
    Classifies queries into processing types:
    - DOCUMENT_QUERY: Single document question
    - DATA_QUERY: Structured data / CSV question
    - MULTI_DOCUMENT_QUERY: Cross-document comparison
    - GENERAL_QUERY: General knowledge question
    """
    
    # Keywords that suggest data/CSV queries
    DATA_KEYWORDS = {
        "calculate", "sum", "average", "total", "count", "maximum", "minimum",
        "median", "percentage", "growth", "revenue", "profit", "sales",
        "quarter", "q1", "q2", "q3", "q4", "year-over-year", "yoy",
        "how much", "how many", "what was the", "what is the",
        "top", "bottom", "highest", "lowest", "rank",
    }
    
    # Keywords that suggest multi-document comparison
    COMPARISON_KEYWORDS = {
        "compare", "comparison", "versus", "vs", "difference", "differences",
        "between", "contrast", "relative", "compared to", "similarities",
        "both", "each", "respectively",
    }
    
    def classify(self, query: str, has_csv: bool = False, document_count: int = 1) -> str:
        """
        Classify a query into a processing type.
        Uses heuristic keyword matching (fast, no LLM call needed).
        """
        query_lower = query.lower()
        
        # Check for data query indicators
        if has_csv and any(kw in query_lower for kw in self.DATA_KEYWORDS):
            logger.info("Query classified as DATA_QUERY", query=query[:50])
            return "DATA_QUERY"
        
        # Check for multi-document comparison
        if document_count > 1 and any(kw in query_lower for kw in self.COMPARISON_KEYWORDS):
            logger.info("Query classified as MULTI_DOCUMENT_QUERY", query=query[:50])
            return "MULTI_DOCUMENT_QUERY"
        
        # Default to document query
        logger.info("Query classified as DOCUMENT_QUERY", query=query[:50])
        return "DOCUMENT_QUERY"
