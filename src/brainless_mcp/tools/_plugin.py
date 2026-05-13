"""Plugin management tools."""

from __future__ import annotations

from typing import Any

from ..core.client import UnraidClient

_LIST_PLUGINS = """
query Plugins {
  plugins {
    name author version description url installed
  }
}
"""

_INSTALL_PLUGIN = """
mutation InstallPlugin($url: String!) {
  pluginInstall(url: $url) { success message }
}
"""

_UPDATE_PLUGIN = """
mutation UpdatePlugin($name: String!) {
  pluginUpdate(name: $name) { success message }
}
"""

_UPDATE_ALL_PLUGINS = """
mutation UpdateAllPlugins {
  pluginUpdateAll { success message count }
}
"""

_REMOVE_PLUGIN = """
mutation RemovePlugin($name: String!) {
  pluginRemove(name: $name) { success message }
}
"""

_CHECK_UPDATES = """
query CheckPluginUpdates {
  pluginUpdates { name currentVersion newVersion hasUpdate }
}
"""


async def handle(client: UnraidClient, subaction: str, params: dict[str, Any]) -> Any:
    match subaction:
        case "list":
            return await client.query(_LIST_PLUGINS, cache=True)
        case "install":
            return await client.mutate(_INSTALL_PLUGIN, {"url": params["url"]}, "plugins")
        case "update":
            return await client.mutate(_UPDATE_PLUGIN, {"name": params["name"]}, "plugins")
        case "update_all":
            return await client.mutate(_UPDATE_ALL_PLUGINS, "plugins")
        case "remove":
            return await client.mutate(_REMOVE_PLUGIN, {"name": params["name"]}, "plugins")
        case "check_updates":
            return await client.query(_CHECK_UPDATES, cache=False)
        case _:
            return {"error": f"Unknown plugin subaction: {subaction}"}
