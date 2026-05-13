"""Array and storage management tools."""

from __future__ import annotations

from typing import Any

from ..core.client import UnraidClient

_ARRAY_STATUS = """
query ArrayStatus {
  array {
    state
    capacity { kilobytes { total free used } bytes { total free used } }
    disks {
      id name device fsType size temp status
    }
    parities {
      id name device size status syncErrors syncAction
    }
  }
}
"""

_ARRAY_START = """
mutation ArrayStart {
  arrayStart { success message }
}
"""

_ARRAY_STOP = """
mutation ArrayStop {
  arrayStop { success message }
}
"""

_PARITY_CHECK_START = """
mutation ParityCheck($correct: Boolean, $noCorrectedErrors: Boolean) {
  parityCheck(correct: $correct, noCorrectedErrors: $noCorrectedErrors) {
    success message
  }
}
"""

_PARITY_CHECK_PAUSE = """
mutation ParityPause {
  parityCheckPause { success message }
}
"""

_PARITY_CHECK_RESUME = """
mutation ParityResume {
  parityCheckResume { success message }
}
"""

_PARITY_CHECK_CANCEL = """
mutation ParityCancel {
  parityCheckCancel { success message }
}
"""

_SHARES_LIST = """
query Shares {
  shares {
    name comment security useCache allocator splitLevel
    free size
    diskInclude diskExclude diskPrimary
  }
}
"""

_SHARE_CREATE = """
mutation ShareCreate($name: String!, $comment: String, $security: String, $cache: String) {
  shareAdd(name: $name, comment: $comment, security: $security, useCache: $cache) {
    success message
  }
}
"""

_SHARE_UPDATE = """
mutation ShareUpdate($name: String!, $comment: String, $security: String, $cache: String) {
  shareEdit(name: $name, comment: $comment, security: $security, useCache: $cache) {
    success message
  }
}
"""

_SHARE_DELETE = """
mutation ShareDelete($name: String!) {
  shareDelete(name: $name) { success message }
}
"""

_DISK_DETAILS = """
query DiskDetails($id: String!) {
  disk(id: $id) {
    id name device vendor model serial size
    rotational smartStatus temp
    reads writes errors
  }
}
"""

_REMOVE_DISK = """
mutation RemoveDisk($id: String!) {
  diskRemove(id: $id) { success message }
}
"""

_CLEAR_DISK_STATS = """
mutation ClearDiskStats($id: String!) {
  diskClearStats(id: $id) { success message }
}
"""

_SMART_TEST = """
mutation SmartTest($id: String!, $type: String!) {
  diskSmartTest(id: $id, type: $type) { success message }
}
"""

_SMART_REPORT = """
query SmartReport($id: String!) {
  diskSmartReport(id: $id) { report }
}
"""


async def handle(client: UnraidClient, subaction: str, params: dict[str, Any]) -> Any:
    match subaction:
        case "status":
            return await client.query(_ARRAY_STATUS, cache=False)
        case "start":
            return await client.mutate(_ARRAY_START, invalidate_prefix="array")
        case "stop":
            return await client.mutate(_ARRAY_STOP, invalidate_prefix="array")
        case "parity_check":
            return await client.mutate(
                _PARITY_CHECK_START,
                {
                    "correct": params.get("correct", False),
                    "noCorrectedErrors": params.get("no_corrected_errors", False),
                },
            )
        case "parity_pause":
            return await client.mutate(_PARITY_CHECK_PAUSE)
        case "parity_resume":
            return await client.mutate(_PARITY_CHECK_RESUME)
        case "parity_cancel":
            return await client.mutate(_PARITY_CHECK_CANCEL)
        case "shares":
            return await client.query(_SHARES_LIST, cache=True)
        case "create_share":
            return await client.mutate(
                _SHARE_CREATE,
                {
                    "name": params["name"],
                    "comment": params.get("comment", ""),
                    "security": params.get("security", "public"),
                    "cache": params.get("cache", "no"),
                },
                "shares",
            )
        case "update_share":
            return await client.mutate(
                _SHARE_UPDATE,
                {
                    "name": params["name"],
                    "comment": params.get("comment"),
                    "security": params.get("security"),
                    "cache": params.get("cache"),
                },
                "shares",
            )
        case "delete_share":
            return await client.mutate(_SHARE_DELETE, {"name": params["name"]}, "shares")
        case "disk_details":
            return await client.disk_query(_DISK_DETAILS, {"id": params["id"]})
        case "remove_disk":
            return await client.mutate(_REMOVE_DISK, {"id": params["id"]}, "array")
        case "clear_disk_stats":
            return await client.mutate(_CLEAR_DISK_STATS, {"id": params["id"]}, "array")
        case "smart_test":
            return await client.mutate(
                _SMART_TEST,
                {"id": params["id"], "type": params.get("type", "short")},
            )
        case "smart_report":
            return await client.disk_query(_SMART_REPORT, {"id": params["id"]})
        case _:
            return {"error": f"Unknown array subaction: {subaction}"}
