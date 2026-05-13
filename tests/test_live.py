"""Tests for the live subscription handler (no real WebSocket needed)."""

import pytest
from brainless_mcp.tools import _live


@pytest.fixture(autouse=True)
def reset_live_state():
    """Reset global subscription state between tests."""
    _live._active.clear()
    _live._buffers.clear()
    yield
    for _, (task, _) in list(_live._active.items()):
        task.cancel()
    _live._active.clear()
    _live._buffers.clear()


@pytest.mark.asyncio
async def test_list_shows_available_subscriptions(mock_client):
    result = await _live.handle(mock_client, "list", {})
    assert "available" in result
    assert "cpu" in result["available"]
    assert result["active"] == []


@pytest.mark.asyncio
async def test_start_creates_task(mock_client):
    result = await _live.handle(mock_client, "start", {"name": "cpu"})
    assert result["status"] == "started"
    assert "cpu" in _live._active


@pytest.mark.asyncio
async def test_start_already_running(mock_client):
    await _live.handle(mock_client, "start", {"name": "cpu"})
    result = await _live.handle(mock_client, "start", {"name": "cpu"})
    assert result["status"] == "already_running"


@pytest.mark.asyncio
async def test_stop_removes_task(mock_client):
    await _live.handle(mock_client, "start", {"name": "cpu"})
    result = await _live.handle(mock_client, "stop", {"name": "cpu"})
    assert result["status"] == "stopped"
    assert "cpu" not in _live._active


@pytest.mark.asyncio
async def test_stop_not_running_returns_error(mock_client):
    result = await _live.handle(mock_client, "stop", {"name": "cpu"})
    assert "error" in result


@pytest.mark.asyncio
async def test_read_empty_buffer(mock_client):
    await _live.handle(mock_client, "start", {"name": "memory"})
    result = await _live.handle(mock_client, "read", {"name": "memory"})
    assert result["count"] == 0
    assert result["data"] == []


@pytest.mark.asyncio
async def test_read_unknown_sub_returns_error(mock_client):
    result = await _live.handle(mock_client, "read", {"name": "cpu"})
    assert "error" in result


@pytest.mark.asyncio
async def test_start_unknown_name_returns_error(mock_client):
    result = await _live.handle(mock_client, "start", {"name": "nope"})
    assert "error" in result


@pytest.mark.asyncio
async def test_start_all_creates_all_tasks(mock_client):
    result = await _live.handle(mock_client, "start_all", {})
    assert len(result["subscriptions"]) == len(_live._SUBS)


@pytest.mark.asyncio
async def test_stop_all_clears_tasks(mock_client):
    await _live.handle(mock_client, "start_all", {})
    result = await _live.handle(mock_client, "stop_all", {})
    assert _live._active == {}
    assert len(result["subscriptions"]) > 0
