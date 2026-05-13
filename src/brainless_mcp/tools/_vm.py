"""Virtual machine management tools."""

from __future__ import annotations

from typing import Any

from ..core.client import UnraidClient

_LIST_VMS = """
query ListVMs {
  vms {
    domain {
      name uuid state
      coreCount maxMemory
      autostart
    }
  }
}
"""

_VM_START = """
mutation VmStart($name: String!) {
  domainStart(name: $name) { success message }
}
"""

_VM_STOP = """
mutation VmStop($name: String!) {
  domainStop(name: $name) { success message }
}
"""

_VM_PAUSE = """
mutation VmPause($name: String!) {
  domainSuspend(name: $name) { success message }
}
"""

_VM_RESUME = """
mutation VmResume($name: String!) {
  domainResume(name: $name) { success message }
}
"""

_VM_REBOOT = """
mutation VmReboot($name: String!) {
  domainReboot(name: $name) { success message }
}
"""

_VM_FORCE_STOP = """
mutation VmForceStop($name: String!) {
  domainDestroy(name: $name) { success message }
}
"""

_VM_RESET = """
mutation VmReset($name: String!) {
  domainReset(name: $name) { success message }
}
"""

_VM_REMOVE = """
mutation VmRemove($name: String!, $deleteDisks: Boolean) {
  domainUndefine(name: $name, deleteDisks: $deleteDisks) { success message }
}
"""

_VM_AUTOSTART = """
mutation VmAutostart($name: String!, $enable: Boolean!) {
  domainSetAutostart(name: $name, enable: $enable) { success message }
}
"""


async def handle(client: UnraidClient, subaction: str, params: dict[str, Any]) -> Any:
    match subaction:
        case "list":
            return await client.query(_LIST_VMS, cache=False)
        case "start":
            return await client.mutate(_VM_START, {"name": params["name"]}, "vms")
        case "stop":
            return await client.mutate(_VM_STOP, {"name": params["name"]}, "vms")
        case "pause":
            return await client.mutate(_VM_PAUSE, {"name": params["name"]}, "vms")
        case "resume":
            return await client.mutate(_VM_RESUME, {"name": params["name"]}, "vms")
        case "reboot":
            return await client.mutate(_VM_REBOOT, {"name": params["name"]}, "vms")
        case "force_stop":
            return await client.mutate(_VM_FORCE_STOP, {"name": params["name"]}, "vms")
        case "reset":
            return await client.mutate(_VM_RESET, {"name": params["name"]}, "vms")
        case "remove":
            return await client.mutate(
                _VM_REMOVE,
                {"name": params["name"], "deleteDisks": params.get("delete_disks", False)},
                "vms",
            )
        case "set_autostart":
            return await client.mutate(
                _VM_AUTOSTART,
                {"name": params["name"], "enable": params["enable"]},
                "vms",
            )
        case _:
            return {"error": f"Unknown vm subaction: {subaction}"}
