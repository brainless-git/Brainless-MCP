"""Tests for the array tool handler."""

import pytest
from brainless_mcp.tools._array import handle


@pytest.mark.asyncio
async def test_status_calls_query(mock_client):
    await handle(mock_client, "status", {})
    mock_client.query.assert_called_once()


@pytest.mark.asyncio
async def test_start_calls_mutate(mock_client):
    await handle(mock_client, "start", {})
    mock_client.mutate.assert_called_once()


@pytest.mark.asyncio
async def test_parity_check_defaults(mock_client):
    await handle(mock_client, "parity_check", {})
    args = mock_client.mutate.call_args[0]
    assert args[1]["correct"] is False
    assert args[1]["noCorrectedErrors"] is False


@pytest.mark.asyncio
async def test_disk_details_uses_disk_query(mock_client):
    await handle(mock_client, "disk_details", {"id": "sda"})
    mock_client.disk_query.assert_called_once()


@pytest.mark.asyncio
async def test_smart_report_uses_disk_query(mock_client):
    await handle(mock_client, "smart_report", {"id": "sda"})
    mock_client.disk_query.assert_called_once()


@pytest.mark.asyncio
async def test_unknown_subaction_returns_error(mock_client):
    result = await handle(mock_client, "unknown", {})
    assert "error" in result
