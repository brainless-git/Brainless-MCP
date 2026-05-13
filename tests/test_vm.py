"""Tests for the VM tool handler."""

import pytest
from brainless_mcp.tools._vm import handle


@pytest.mark.asyncio
async def test_list_calls_query(mock_client):
    await handle(mock_client, "list", {})
    mock_client.query.assert_called_once()


@pytest.mark.asyncio
async def test_start_calls_mutate(mock_client):
    await handle(mock_client, "start", {"name": "Windows10"})
    mock_client.mutate.assert_called_once()
    args = mock_client.mutate.call_args[0]
    assert args[1]["name"] == "Windows10"


@pytest.mark.asyncio
async def test_force_stop_calls_mutate(mock_client):
    await handle(mock_client, "force_stop", {"name": "Windows10"})
    mock_client.mutate.assert_called_once()


@pytest.mark.asyncio
async def test_remove_defaults_delete_disks_false(mock_client):
    await handle(mock_client, "remove", {"name": "Windows10"})
    args = mock_client.mutate.call_args[0]
    assert args[1]["deleteDisks"] is False


@pytest.mark.asyncio
async def test_unknown_subaction_returns_error(mock_client):
    result = await handle(mock_client, "bogus", {})
    assert "error" in result
