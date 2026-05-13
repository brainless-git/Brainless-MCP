"""Tests for the docker tool handler."""

import pytest
from brainless_mcp.tools._docker import handle


@pytest.mark.asyncio
async def test_list_calls_query(mock_client):
    await handle(mock_client, "list", {})
    mock_client.query.assert_called_once()


@pytest.mark.asyncio
async def test_start_calls_mutate(mock_client):
    await handle(mock_client, "start", {"id": "abc123"})
    mock_client.mutate.assert_called_once()
    args = mock_client.mutate.call_args[0]
    assert args[1]["id"] == "abc123"


@pytest.mark.asyncio
async def test_stop_calls_mutate(mock_client):
    await handle(mock_client, "stop", {"id": "abc123"})
    mock_client.mutate.assert_called_once()


@pytest.mark.asyncio
async def test_logs_uses_query(mock_client):
    await handle(mock_client, "logs", {"id": "abc123", "tail": 50})
    mock_client.query.assert_called_once()


@pytest.mark.asyncio
async def test_unknown_subaction_returns_error(mock_client):
    result = await handle(mock_client, "nonexistent", {})
    assert "error" in result
