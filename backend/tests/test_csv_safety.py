"""Tests for CSV safety — ensuring generated queries cannot be destructive."""

import re
import pytest
from app.services.csv_analyzer import DANGEROUS_PATTERNS, CSVAnalyzer


class TestCSVSafety:
    """Test that dangerous operations are rejected."""

    def test_import_blocked(self):
        """Import statements are blocked."""
        for pattern in DANGEROUS_PATTERNS:
            if "import" in pattern:
                assert re.search(pattern, "import os", re.IGNORECASE)

    def test_exec_blocked(self):
        """exec() calls are blocked."""
        for pattern in DANGEROUS_PATTERNS:
            if "exec" in pattern:
                assert re.search(pattern, "exec('malicious')", re.IGNORECASE)

    def test_eval_blocked(self):
        """eval() calls are blocked."""
        for pattern in DANGEROUS_PATTERNS:
            if "eval" in pattern and "__" not in pattern:
                assert re.search(pattern, "eval('code')", re.IGNORECASE)

    def test_os_blocked(self):
        """os module access is blocked."""
        for pattern in DANGEROUS_PATTERNS:
            if pattern == r"os\.":
                assert re.search(pattern, "os.system('rm -rf /')")

    def test_sql_injection_blocked(self):
        """SQL injection attempts are blocked."""
        dangerous_ops = ["DROP TABLE users", "DELETE FROM data", "UPDATE config SET"]
        for op in dangerous_ops:
            matched = any(re.search(p, op, re.IGNORECASE) for p in DANGEROUS_PATTERNS)
            assert matched, f"Should block: {op}"

    def test_safe_pandas_allowed(self):
        """Safe pandas operations are allowed."""
        safe_ops = [
            "df.groupby('region')['revenue'].sum()",
            "df['revenue'].mean()",
            "df.sort_values('revenue', ascending=False).head(5)",
            "df.describe()",
        ]
        for op in safe_ops:
            matched = any(re.search(p, op, re.IGNORECASE) for p in DANGEROUS_PATTERNS)
            assert not matched, f"Should allow: {op}"

    def test_dunder_blocked(self):
        """Dunder attribute access is blocked."""
        for pattern in DANGEROUS_PATTERNS:
            if "__" in pattern:
                assert re.search(pattern, "__import__('os')")
