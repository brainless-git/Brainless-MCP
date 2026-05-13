"""Tests for the health tool handler."""

import pytest
from brainless_mcp.tools._health import handle


@pytest.mark.asyncio
async def test_ping_returns_ok(mock_client):
    result = await handle(mock_client, "ping", {})
    assert result["status"] == "ok"
    assert "latency_ms" in result


@pytest.mark.asyncio
async def test_ping_returns_error_on_failure(mock_client):
    mock_client.query.side_effect = Exception("connection refused")
    result = await handle(mock_client, "ping", {})
    assert result["status"] == "error"
    assert "connection refused" in result["detail"]


@pytest.mark.asyncio
async def test_connection_test_reports_settings(mock_client):
    result = await handle(mock_client, "connection_test", {})
    assert "api_url" in result
    assert "connected" in result


@pytest.mark.asyncio
async def test_config_returns_settings(mock_client):
    result = await handle(mock_client, "config", {})
    assert "api_url" in result
    assert "transport" in result


@pytest.mark.asyncio
async def test_unknown_subaction_returns_error(mock_client):
    result = await handle(mock_client, "bogus", {})
    assert "error" in result
