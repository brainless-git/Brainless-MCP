"""Main consolidated 'unraid' tool — routes action+subaction to domain handlers."""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from ..core.client import UnraidClient
from ..core.exceptions import ConfirmationRequired, UnraidError
from ..core.guards import require_confirm
from . import _array, _docker, _health, _live, _notification, _plugin, _setting, _system, _user, _vm

logger = logging.getLogger(__name__)

Action = Literal[
    "system",
    "health",
    "docker",
    "vm",
    "array",
    "notification",
    "user",
    "plugin",
    "setting",
    "live",
]

_HANDLERS = {
    "system": _system.handle,
    "health": _health.handle,
    "docker": _docker.handle,
    "vm": _vm.handle,
    "array": _array.handle,
    "notification": _notification.handle,
    "user": _user.handle,
    "plugin": _plugin.handle,
    "setting": _setting.handle,
    "live": _live.handle,
}

# Subaction catalogue per action (for help output)
_SUBACTIONS: dict[str, list[str]] = {
    "system": ["overview", "info", "cpu", "memory", "network", "ups"],
    "health": ["ping", "connection_test", "config"],
    "docker": [
        "list", "images", "networks",
        "start", "stop", "restart", "pause", "unpause",
        "remove", "logs", "update_all", "set_autostart",
    ],
    "vm": [
        "list",
        "start", "stop", "pause", "resume", "reboot",
        "force_stop", "reset", "remove", "set_autostart",
    ],
    "array": [
        "status", "start", "stop",
        "parity_check", "parity_pause", "parity_resume", "parity_cancel",
        "shares", "create_share", "update_share", "delete_share",
        "disk_details", "remove_disk", "clear_disk_stats",
        "smart_test", "smart_report",
    ],
    "notification": [
        "list", "archived", "add",
        "mark_read", "mark_all_read",
        "delete", "delete_all", "archive",
    ],
    "user": ["list", "add", "update", "delete", "set_role"],
    "plugin": ["list", "install", "update", "update_all", "remove", "check_updates"],
    "setting": ["get", "update", "network", "reboot", "shutdown", "ups_config", "configure_ups"],
    "live": ["list", "start", "stop", "read", "start_all", "stop_all"],
}


def _truncate(data: Any, max_bytes: int = 524_288) -> str:
    """Serialise data to JSON and truncate if over max_bytes."""
    text = json.dumps(data, default=str, indent=2)
    if len(text.encode()) > max_bytes:
        text = text[:max_bytes] + "\n... [truncated]"
    return text


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="unraid",
        description=(
            "Full-control tool for managing an Unraid server. "
            "Use action + subaction to target a specific domain and operation.\n\n"
            "Actions: system, health, docker, vm, array, notification, user, plugin, setting, live\n\n"
            "Examples:\n"
            "  action='docker' subaction='list'\n"
            "  action='vm' subaction='start' params={'name': 'Windows10'}\n"
            "  action='array' subaction='status'\n"
            "  action='array' subaction='stop' confirm=True\n"
            "  action='docker' subaction='remove' params={'id': 'abc123'} confirm=True\n"
            "  action='live' subaction='start' params={'name': 'cpu'}\n"
            "  action='health' subaction='ping'\n\n"
            "Pass confirm=True for destructive operations (stop array, remove containers/VMs, etc.)."
        ),
    )
    async def unraid(
        action: Annotated[Action, "Domain area to target"],
        subaction: Annotated[str, "Specific operation within the domain"],
        params: Annotated[
            dict[str, Any],
            "Operation parameters (e.g. {'id': 'container_id'}, {'name': 'vm_name'})",
        ] = {},
        confirm: Annotated[
            bool,
            "Set to True to confirm destructive operations",
        ] = False,
    ) -> str:
        # Validate action
        handler = _HANDLERS.get(action)
        if handler is None:
            raise ToolError(
                f"Unknown action '{action}'. Valid actions: {list(_HANDLERS)}"
            )

        # Validate subaction
        valid_subs = _SUBACTIONS.get(action, [])
        if valid_subs and subaction not in valid_subs:
            raise ToolError(
                f"Unknown subaction '{subaction}' for action '{action}'. "
                f"Valid subactions: {valid_subs}"
            )

        # Safety guard
        try:
            require_confirm(action, subaction, confirm)
        except ConfirmationRequired as exc:
            raise ToolError(str(exc)) from exc

        # Execute
        client = UnraidClient()
        try:
            result = await handler(client, subaction, params)
        except ConfirmationRequired as exc:
            raise ToolError(str(exc)) from exc
        except UnraidError as exc:
            logger.error("Unraid API error [%s::%s]: %s", action, subaction, exc)
            raise ToolError(f"Unraid API error: {exc}") from exc
        except Exception as exc:
            logger.exception("Unexpected error [%s::%s]", action, subaction)
            raise ToolError(f"Unexpected error: {exc}") from exc

        return _truncate(result)

    @mcp.tool(
        name="unraid_help",
        description="List all available actions and subactions for the unraid tool.",
    )
    async def unraid_help(
        action: Annotated[str, "Filter to a specific action (optional)"] = "",
    ) -> str:
        if action:
            subs = _SUBACTIONS.get(action)
            if subs is None:
                raise ToolError(f"Unknown action '{action}'. Valid: {list(_SUBACTIONS)}")
            return json.dumps({action: subs}, indent=2)
        return json.dumps(_SUBACTIONS, indent=2)
