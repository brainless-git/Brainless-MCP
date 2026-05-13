"""FastMCP server construction with middleware."""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any, Callable

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from .config import get_settings
from .tools import register_tools

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.brainless_mcp_log_level.upper(), logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if settings.brainless_mcp_log_file:
        handlers.append(logging.FileHandler(settings.brainless_mcp_log_file))
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def _check_bearer(token: str) -> bool:
    """Return True if the bearer token is valid (or auth is disabled)."""
    settings = get_settings()
    configured = settings.brainless_mcp_bearer_token
    if not configured:
        return True
    return token == configured


def create_server() -> FastMCP:
    _setup_logging()
    settings = get_settings()

    mcp: FastMCP = FastMCP(
        name="Brainless MCP",
        instructions=(
            "Full-control MCP server for Unraid. "
            "Use the 'unraid' tool with action+subaction parameters. "
            "Call 'unraid_help' with no arguments to list everything available."
        ),
    )

    register_tools(mcp)

    if settings.unraid_auto_start_subscriptions:
        import asyncio
        from .tools._live import _SUBS, _active, _buffers, _run_subscription

        @mcp.on_startup
        async def _start_subs() -> None:
            for name, gql in _SUBS.items():
                buf: list[Any] = []
                _buffers[name] = buf
                task = asyncio.create_task(_run_subscription(name, gql, buf))
                _active[name] = (task, buf)
            logger.info("Auto-started %d subscriptions.", len(_SUBS))

    return mcp
