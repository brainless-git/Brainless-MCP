"""Entry point for Brainless MCP server."""

from __future__ import annotations

import sys

from .config import get_settings
from .core.cert_manager import ensure_certificate, is_configured
from .server import create_server


def _resolve_ssl(settings) -> dict:  # type: ignore[type-arg]
    """Return uvicorn SSL kwargs, running ACME renewal if configured."""
    if is_configured(settings):
        certfile, keyfile = ensure_certificate(settings)
        if certfile and keyfile:
            return {"ssl_certfile": certfile, "ssl_keyfile": keyfile}
        return {}

    # Manual cert paths
    certfile = settings.brainless_mcp_ssl_certfile
    keyfile = settings.brainless_mcp_ssl_keyfile
    if not certfile and not keyfile:
        return {}
    if not certfile or not keyfile:
        print(
            "Error: both BRAINLESS_MCP_SSL_CERTFILE and BRAINLESS_MCP_SSL_KEYFILE "
            "must be set to enable HTTPS.",
            file=sys.stderr,
        )
        sys.exit(1)
    return {"ssl_certfile": certfile, "ssl_keyfile": keyfile}


def run() -> None:
    settings = get_settings()
    mcp = create_server()

    transport = settings.brainless_mcp_transport.lower()
    ssl = _resolve_ssl(settings)

    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport in ("http", "streamable-http"):
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=settings.brainless_mcp_port,
            **ssl,
        )
    elif transport == "sse":
        mcp.run(
            transport="sse",
            host="0.0.0.0",
            port=settings.brainless_mcp_port,
            **ssl,
        )
    else:
        print(f"Unknown transport: {transport}. Use: stdio | http | sse", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
