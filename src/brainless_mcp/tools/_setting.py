"""System settings tools."""

from __future__ import annotations

from typing import Any

from ..core.client import UnraidClient

_GET_SETTINGS = """
query GetSettings {
  settings {
    shareMode shareFloor
    defaultShare
    syslog { server port protocol }
    ntp { server1 server2 }
    smb { workgroup netbios enabled }
    nfs { enabled version }
    ssh { enabled port }
  }
}
"""

_UPDATE_SETTING = """
mutation UpdateSetting($key: String!, $value: String!) {
  settingUpdate(key: $key, value: $value) { success message }
}
"""

_GET_NETWORK = """
query NetworkSettings {
  networkSettings {
    hostname description
    dns1 dns2
    interfaces {
      name dhcp ip netmask gateway
    }
  }
}
"""

_REBOOT = """
mutation SystemReboot {
  systemReboot { success message }
}
"""

_SHUTDOWN = """
mutation SystemShutdown {
  systemShutdown { success message }
}
"""

_GET_UPS_CONFIG = """
query UpsConfig {
  ups { config { device driver cable type mode } }
}
"""

_CONFIGURE_UPS = """
mutation ConfigureUps($device: String!, $driver: String!, $cable: String, $type: String) {
  upsSetConfig(device: $device, driver: $driver, cable: $cable, type: $type) {
    success message
  }
}
"""


async def handle(client: UnraidClient, subaction: str, params: dict[str, Any]) -> Any:
    match subaction:
        case "get":
            return await client.query(_GET_SETTINGS, cache=True)
        case "update":
            return await client.mutate(
                _UPDATE_SETTING,
                {"key": params["key"], "value": str(params["value"])},
            )
        case "network":
            return await client.query(_GET_NETWORK, cache=True)
        case "reboot":
            return await client.mutate(_REBOOT)
        case "shutdown":
            return await client.mutate(_SHUTDOWN)
        case "ups_config":
            return await client.query(_GET_UPS_CONFIG, cache=True)
        case "configure_ups":
            return await client.mutate(
                _CONFIGURE_UPS,
                {
                    "device": params["device"],
                    "driver": params["driver"],
                    "cable": params.get("cable", "usb"),
                    "type": params.get("type", "usb"),
                },
            )
        case _:
            return {"error": f"Unknown setting subaction: {subaction}"}
