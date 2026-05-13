"""Docker container management tools."""

from __future__ import annotations

from typing import Any

from ..core.client import UnraidClient

_LIST_CONTAINERS = """
query DockerContainers {
  docker {
    containers {
      id name image status state
      autoStart ports { ip privatePort publicPort type }
    }
  }
}
"""

_LIST_IMAGES = """
query DockerImages {
  docker {
    images { id repository tag size created }
  }
}
"""

_LIST_NETWORKS = """
query DockerNetworks {
  docker {
    networks { id name driver scope }
  }
}
"""

_CONTAINER_START = """
mutation DockerStart($id: String!) {
  dockerContainerStart(id: $id) { success message }
}
"""

_CONTAINER_STOP = """
mutation DockerStop($id: String!) {
  dockerContainerStop(id: $id) { success message }
}
"""

_CONTAINER_RESTART = """
mutation DockerRestart($id: String!) {
  dockerContainerRestart(id: $id) { success message }
}
"""

_CONTAINER_PAUSE = """
mutation DockerPause($id: String!) {
  dockerContainerPause(id: $id) { success message }
}
"""

_CONTAINER_UNPAUSE = """
mutation DockerUnpause($id: String!) {
  dockerContainerUnpause(id: $id) { success message }
}
"""

_CONTAINER_REMOVE = """
mutation DockerRemove($id: String!, $force: Boolean) {
  dockerContainerRemove(id: $id, force: $force) { success message }
}
"""

_CONTAINER_LOGS = """
query DockerLogs($id: String!, $tail: Int) {
  dockerContainerLogs(id: $id, tail: $tail) { logs }
}
"""

_UPDATE_ALL = """
mutation DockerUpdateAll {
  dockerUpdateAll { success message }
}
"""

_TOGGLE_AUTOSTART = """
mutation DockerToggleAutoStart($id: String!, $autoStart: Boolean!) {
  dockerContainerSetAutoStart(id: $id, autoStart: $autoStart) { success message }
}
"""


async def handle(client: UnraidClient, subaction: str, params: dict[str, Any]) -> Any:
    match subaction:
        case "list":
            return await client.query(_LIST_CONTAINERS, cache=False)
        case "images":
            return await client.query(_LIST_IMAGES, cache=True)
        case "networks":
            return await client.query(_LIST_NETWORKS, cache=True)
        case "start":
            return await client.mutate(_CONTAINER_START, {"id": params["id"]}, "docker")
        case "stop":
            return await client.mutate(_CONTAINER_STOP, {"id": params["id"]}, "docker")
        case "restart":
            return await client.mutate(_CONTAINER_RESTART, {"id": params["id"]}, "docker")
        case "pause":
            return await client.mutate(_CONTAINER_PAUSE, {"id": params["id"]}, "docker")
        case "unpause":
            return await client.mutate(_CONTAINER_UNPAUSE, {"id": params["id"]}, "docker")
        case "remove":
            return await client.mutate(
                _CONTAINER_REMOVE,
                {"id": params["id"], "force": params.get("force", False)},
                "docker",
            )
        case "logs":
            return await client.query(
                _CONTAINER_LOGS,
                {"id": params["id"], "tail": params.get("tail", 100)},
                cache=False,
            )
        case "update_all":
            return await client.mutate(_UPDATE_ALL, invalidate_prefix="docker")
        case "set_autostart":
            return await client.mutate(
                _TOGGLE_AUTOSTART,
                {"id": params["id"], "autoStart": params["auto_start"]},
                "docker",
            )
        case _:
            return {"error": f"Unknown docker subaction: {subaction}"}
