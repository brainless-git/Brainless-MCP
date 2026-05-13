"""Health and diagnostics tools."""

from __future__ import annotations

import time
from typing import Any

from ..core.client import UnraidClient

_PING = """
query Ping {
  info {
    os { platform }
    versions { unraid }
  }
}
"""


async def handle(client: UnraidClient, subaction: str, params: dict[str, Any]) -> Any:
    match subaction:
        case "ping":
            t0 = time.monotonic()
            try:
                await client.query(_PING, cache=False)
                elapsed = round((time.monotonic() - t0) * 1000, 1)
                return {"status": "ok", "latency_ms": elapsed}
            except Exception as exc:
                return {"status": "error", "detail": str(exc)}

        case "connection_test":
            from ..config import get_settings
            s = get_settings()
            result: dict[str, Any] = {
                "api_url": s.unraid_api_url,
                "api_key_set": bool(s.unraid_api_key),
                "ssl_verify": s.ssl_verify,
            }
            t0 = time.monotonic()
            try:
                await client.query(_PING, cache=False)
                result["connected"] = True
                result["latency_ms"] = round((time.monotonic() - t0) * 1000, 1)
            except Exception as exc:
                result["connected"] = False
                result["error"] = str(exc)
            return result

        case "config":
            from ..config import get_settings
            s = get_settings()
            return {
                "api_url": s.unraid_api_url,
                "api_key_set": bool(s.unraid_api_key),
                "ssl_verify": s.ssl_verify,
                "transport": s.brainless_mcp_transport,
                "log_level": s.brainless_mcp_log_level,
                "auto_start_subscriptions": s.unraid_auto_start_subscriptions,
            }

        case _:
            return {"error": f"Unknown health subaction: {subaction}"}
