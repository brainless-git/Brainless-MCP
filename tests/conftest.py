"""Shared fixtures for Brainless MCP tests."""

import os
import pytest

# Ensure env is set before importing settings (which caches on import)
os.environ.setdefault("UNRAID_API_URL", "https://tower.local")
os.environ.setdefault("UNRAID_API_KEY", "test-key")
os.environ.setdefault("UNRAID_VERIFY_SSL", "false")
os.environ.setdefault("BRAINLESS_MCP_BEARER_TOKEN", "test-token")


@pytest.fixture
def mock_client():
    """Return a MagicMock UnraidClient with async query/mutate."""
    from unittest.mock import AsyncMock, MagicMock
    client = MagicMock()
    client.query = AsyncMock(return_value={})
    client.mutate = AsyncMock(return_value={"success": True, "message": "ok"})
    client.disk_query = AsyncMock(return_value={})
    return client
