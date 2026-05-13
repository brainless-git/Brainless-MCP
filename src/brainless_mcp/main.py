"""Entry point for Brainless MCP server."""

from __future__ import annotations

import sys

from .config import get_settings
from .server import create_server


def run() -> None:
    settings = get_settings()
    mcp = create_server()

    transport = settings.brainless_mcp_transport.lower()

    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport in ("http", "streamable-http"):
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=settings.brainless_mcp_port,
        )
    elif transport == "sse":
        mcp.run(
            transport="sse",
            host="0.0.0.0",
            port=settings.brainless_mcp_port,
        )
    else:
        print(f"Unknown transport: {transport}. Use: stdio | http | sse", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
