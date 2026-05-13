"""Tests for the destructive-action safety guards."""

import pytest
from brainless_mcp.core.guards import require_confirm, DESTRUCTIVE_ACTIONS
from brainless_mcp.core.exceptions import ConfirmationRequired


def test_safe_action_passes_without_confirm():
    require_confirm("docker", "list", confirm=False)  # should not raise


def test_destructive_action_raises_without_confirm():
    with pytest.raises(ConfirmationRequired, match="confirm=True"):
        require_confirm("array", "stop_array", confirm=False)


def test_destructive_action_passes_with_confirm():
    require_confirm("array", "stop_array", confirm=True)  # should not raise


def test_vm_force_stop_requires_confirm():
    with pytest.raises(ConfirmationRequired):
        require_confirm("vm", "force_stop", confirm=False)


def test_vm_force_stop_allowed_with_confirm():
    require_confirm("vm", "force_stop", confirm=True)


def test_all_destructive_actions_are_blocked():
    for key in DESTRUCTIVE_ACTIONS:
        action, subaction = key.split("::")
        with pytest.raises(ConfirmationRequired):
            require_confirm(action, subaction, confirm=False)
