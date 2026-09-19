"""
Tests for session isolation and multi-tenant workspace separation.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.workspace import get_current_workspace
from app.models.user import User
from app.models.workspace import Workspace


import anyio


def test_session_workspace_creation():
    """Verify that different session IDs create distinct users and workspaces."""
    async def _test():
        db = AsyncMock()
        
        # First call with session A: no user found, creates user and workspace
        execute_mock_a = MagicMock()
        execute_mock_a.scalar_one_or_none.return_value = None
        db.execute.return_value = execute_mock_a
        
        workspace_a = await get_current_workspace(x_session_id="test_user_a", db=db)
        
        assert workspace_a is not None
        assert "test_use" in workspace_a.name
        
        # Second call with session B
        execute_mock_b = MagicMock()
        execute_mock_b.scalar_one_or_none.return_value = None
        db.execute.return_value = execute_mock_b
        
        workspace_b = await get_current_workspace(x_session_id="test_user_b", db=db)
        
        assert workspace_b is not None
        assert "test_use" in workspace_b.name
        assert workspace_a is not workspace_b

    anyio.run(_test)


def test_default_workspace_fallback():
    """Verify fallback to default workspace when no session ID is supplied."""
    async def _test():
        db = AsyncMock()
        
        execute_mock = MagicMock()
        execute_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = execute_mock
        
        workspace = await get_current_workspace(x_session_id=None, db=db)
        assert workspace.name == "Default Workspace"

    anyio.run(_test)
