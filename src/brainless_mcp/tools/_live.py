"""Live subscription management (WebSocket-based real-time data)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from ..config import get_settings

logger = logging.getLogger(__name__)

# Subscription GraphQL strings
_SUBS: dict[str, str] = {
    "cpu": "subscription { cpuUsage { cores load } }",
    "memory": "subscription { memoryUsage { total free used percent } }",
    "array": "subscription { arrayState { state disks { id name status temp } } }",
    "network": "subscription { networkUsage { interfaces { name rxSec txSec } } }",
    "docker": "subscription { dockerContainerEvents { id name status } }",
    "vm": "subscription { domainEvents { name state } }",
    "notifications": "subscription { notificationAdded { id subject importance } }",
    "parity": "subscription { parityProgress { action percent speed errors } }",
    "disk_temps": "subscription { diskTemps { id name temp status } }",
    "logs": "subscription { syslogLines { timestamp level message } }",
}

# Active subscription tasks: name -> (task, buffer)
_active: dict[str, tuple[asyncio.Task[Any], list[Any]]] = {}
_buffers: dict[str, list[Any]] = {}


async def _run_subscription(name: str, gql: str, buffer: list[Any], max_buffer: int = 100) -> None:
    """Run a WebSocket subscription and push data into the buffer."""
    import websockets

    settings = get_settings()
    ws_url = settings.ws_url
    headers = {"x-api-key": settings.unraid_api_key}

    attempts = 0
    max_attempts = settings.unraid_max_reconnect_attempts
    backoff = 1.0

    while attempts < max_attempts:
        try:
            async with websockets.connect(
                ws_url,
                additional_headers=headers,
                subprotocols=["graphql-ws"],
                ssl=None if str(settings.ssl_verify).lower() == "false" else True,
            ) as ws:
                attempts = 0
                backoff = 1.0
                await ws.send(json.dumps({"type": "connection_init"}))
                await ws.recv()  # connection_ack
                await ws.send(json.dumps({"id": "1", "type": "start", "payload": {"query": gql}}))
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg.get("type") == "data":
                        data = msg.get("payload", {}).get("data")
                        if data is not None:
                            buffer.append(data)
                            if len(buffer) > max_buffer:
                                buffer.pop(0)
        except Exception as exc:
            logger.warning("Subscription '%s' error: %s — retrying in %.1fs", name, exc, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)
            attempts += 1

    logger.error("Subscription '%s' exhausted %d reconnect attempts.", name, max_attempts)


async def handle(client: Any, subaction: str, params: dict[str, Any]) -> Any:
    match subaction:
        case "start":
            name = params.get("name", "")
            if name not in _SUBS:
                return {"error": f"Unknown subscription: {name}. Available: {list(_SUBS)}"}
            if name in _active:
                return {"status": "already_running", "name": name}
            buffer: list[Any] = []
            _buffers[name] = buffer
            task = asyncio.create_task(_run_subscription(name, _SUBS[name], buffer))
            _active[name] = (task, buffer)
            return {"status": "started", "name": name}

        case "stop":
            name = params.get("name", "")
            if name not in _active:
                return {"error": f"Subscription '{name}' is not running."}
            task, _ = _active.pop(name)
            task.cancel()
            _buffers.pop(name, None)
            return {"status": "stopped", "name": name}

        case "read":
            name = params.get("name", "")
            buf = _buffers.get(name)
            if buf is None:
                return {"error": f"Subscription '{name}' not started or no data yet."}
            limit = params.get("limit", 20)
            data = buf[-limit:] if limit else list(buf)
            return {"name": name, "count": len(data), "data": data}

        case "list":
            return {
                "available": list(_SUBS.keys()),
                "active": [
                    {"name": n, "buffered": len(_buffers.get(n, []))} for n in _active
                ],
            }

        case "start_all":
            started = []
            for name, gql in _SUBS.items():
                if name not in _active:
                    buffer = []
                    _buffers[name] = buffer
                    task = asyncio.create_task(_run_subscription(name, gql, buffer))
                    _active[name] = (task, buffer)
                    started.append(name)
            return {"status": "started", "subscriptions": started}

        case "stop_all":
            stopped = list(_active.keys())
            for name, (task, _) in list(_active.items()):
                task.cancel()
            _active.clear()
            _buffers.clear()
            return {"status": "stopped", "subscriptions": stopped}

        case _:
            return {"error": f"Unknown live subaction: {subaction}"}
