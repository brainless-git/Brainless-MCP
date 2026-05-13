"""System info and metrics tools."""

from __future__ import annotations

from typing import Any

from ..core.client import UnraidClient

_SYSTEM_INFO = """
query SystemInfo {
  info {
    os { platform version }
    cpu { brand cores threads }
    memory { total free used }
    uptime
  }
}
"""

_SYSTEM_OVERVIEW = """
query SystemOverview {
  info {
    os { platform version kernelVersion }
    cpu { brand cores threads currentLoad }
    memory { total free used swaptotal swapfree swapused }
    uptime
    versions { unraid }
  }
  network {
    interfaces { name ip4 mac speed type state }
  }
}
"""

_CPU_METRICS = """
query CpuMetrics {
  info {
    cpu { brand cores threads currentLoad }
  }
}
"""

_MEMORY_METRICS = """
query MemoryMetrics {
  info {
    memory { total free used active available swaptotal swapfree swapused }
  }
}
"""

_NETWORK_INFO = """
query NetworkInfo {
  network {
    interfaces { name ip4 ip6 mac speed type state rxSec txSec }
  }
}
"""

_UPS_DEVICES = """
query UpsDevices {
  ups { devices { name model status batteryCharge timeLeft outputVoltage load } }
}
"""


async def handle(client: UnraidClient, subaction: str, params: dict[str, Any]) -> Any:
    match subaction:
        case "overview":
            return await client.query(_SYSTEM_OVERVIEW, cache=True)
        case "info":
            return await client.query(_SYSTEM_INFO, cache=True)
        case "cpu":
            return await client.query(_CPU_METRICS, cache=False)
        case "memory":
            return await client.query(_MEMORY_METRICS, cache=False)
        case "network":
            return await client.query(_NETWORK_INFO, cache=True)
        case "ups":
            return await client.query(_UPS_DEVICES, cache=False)
        case _:
            return {"error": f"Unknown system subaction: {subaction}"}
