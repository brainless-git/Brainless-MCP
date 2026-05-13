"""Safety guards for destructive operations."""

from __future__ import annotations

from .exceptions import ConfirmationRequired

# Actions that require explicit confirm=True before execution
DESTRUCTIVE_ACTIONS: frozenset[str] = frozenset(
    {
        "array::stop_array",
        "array::remove_disk",
        "array::clear_disk_stats",
        "array::format_disk",
        "vm::force_stop",
        "vm::reset",
        "vm::remove",
        "docker::remove",
        "docker::remove_image",
        "notification::delete",
        "notification::delete_all",
        "plugin::remove",
        "user::delete",
        "disk::format",
        "disk::clear",
        "setting::reset_to_defaults",
        "share::delete",
    }
)


def require_confirm(action: str, subaction: str, confirm: bool) -> None:
    """Raise ConfirmationRequired if a destructive action lacks confirm=True."""
    key = f"{action}::{subaction}"
    if key in DESTRUCTIVE_ACTIONS and not confirm:
        raise ConfirmationRequired(
            f"'{key}' is a destructive operation. Pass confirm=True to proceed."
        )
