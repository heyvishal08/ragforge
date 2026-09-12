"""
CSV Analyzer — structured data querying using safe pandas operations.
"""

import os
import re

import pandas as pd
import structlog

from app.core.config import settings
from app.providers.llm_provider import get_llm_provider

logger = structlog.get_logger()

# Dangerous patterns that could indicate injection
DANGEROUS_PATTERNS = [
    r"import\s",
    r"__\w+__",
    r"exec\s*\(",
    r"eval\s*\(",
    r"compile\s*\(",
    r"open\s*\(",
    r"os\.",
    r"sys\.",
    r"subprocess",
    r"shutil",
    r"pathlib",
    r"glob\.",
    r"input\s*\(",
    r"print\s*\(",
    r"del\s",
    r"rm\s",
    r"DROP\s",
    r"DELETE\s",
    r"UPDATE\s",
    r"INSERT\s",
    r"ALTER\s",
    r"TRUNCATE",
]


class CSVAnalyzer:
    """
    Analyzes CSV data using safe pandas operations.
    Generates and validates pandas code, then executes in a restricted sandbox.
    """
    
    def __init__(self):
        self.llm = get_llm_provider()
    
    async def analyze(self, file_path: str, query: str, metadata: dict) -> dict:
        """
        Analyze a CSV file using a natural language query.
        
        Returns:
            {
                "result": str/number/dataframe,
                "operation": str (the generated code),
                "explanation": str,
            }
        """
        df = pd.read_csv(file_path)
        
        # Build schema context
        schema = self._get_schema_info(df)
        
        # Generate pandas operation
        operation = await self._generate_operation(query, schema, df.head(5).to_string())
        
        # Validate safety
        if not self._validate_operation(operation):
            return {
                "result": "Query rejected for safety reasons.",
                "operation": operation,
                "explanation": "The generated operation contained potentially unsafe patterns and was blocked.",
                "safe": False,
            }
        
        # Execute safely
        try:
            result = self._execute_safe(df, operation)
            
            # Generate explanation
            explanation = await self._explain_result(query, operation, str(result))
            
            return {
                "result": str(result),
                "operation": operation,
                "explanation": explanation,
                "safe": True,
            }
        except Exception as e:
            return {
                "result": f"Error executing query: {str(e)}",
                "operation": operation,
                "explanation": f"The operation failed: {str(e)}",
                "safe": True,
            }
    
    def _get_schema_info(self, df: pd.DataFrame) -> str:
        """Get schema information for the dataframe."""
        info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            nunique = df[col].nunique()
            info.append(f"  - {col}: {dtype} ({nunique} unique values)")
        
        return f"Columns:\n" + "\n".join(info) + f"\n\nTotal rows: {len(df)}"
    
    async def _generate_operation(self, query: str, schema: str, sample: str) -> str:
        """Use LLM to generate a safe pandas operation."""
        prompt = f"""Generate a single pandas operation to answer this question about a DataFrame called 'df'.

Schema:
{schema}

Sample data:
{sample}

Question: {query}

Rules:
- Return ONLY the pandas expression (one line), nothing else
- Use only: df[], .groupby(), .sum(), .mean(), .count(), .max(), .min(), .sort_values(), .head(), .tail(), .value_counts(), .describe(), .agg(), .filter(), .query(), .nlargest(), .nsmallest(), .pivot_table()
- Do NOT use: import, exec, eval, open, os, sys, print
- The expression should return a result (Series, DataFrame, or scalar)

pandas expression:"""
        
        response = await self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        
        operation = response["content"].strip()
        # Clean up any markdown formatting
        if operation.startswith("```"):
            operation = operation.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        
        return operation
    
    def _validate_operation(self, operation: str) -> bool:
        """Validate that a generated operation is safe to execute."""
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, operation, re.IGNORECASE):
                logger.warning("Dangerous pattern detected", pattern=pattern, operation=operation)
                return False
        return True
    
    def _execute_safe(self, df: pd.DataFrame, operation: str) -> any:
        """Execute a pandas operation in a restricted namespace."""
        # Restricted namespace — only pandas and the dataframe
        safe_globals = {"__builtins__": {}}
        safe_locals = {"df": df, "pd": pd}
        
        result = eval(operation, safe_globals, safe_locals)
        return result
    
    async def _explain_result(self, query: str, operation: str, result: str) -> str:
        """Generate a natural language explanation of the result."""
        prompt = f"""Briefly explain this data analysis result in 1-2 sentences.

Question: {query}
Operation: {operation}
Result: {result}

Explanation:"""
        
        response = await self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        
        return response["content"].strip()
