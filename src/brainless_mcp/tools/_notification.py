"""Notification management tools."""

from __future__ import annotations

from typing import Any

from ..core.client import UnraidClient

_LIST_NOTIFICATIONS = """
query Notifications($limit: Int, $offset: Int) {
  notifications(limit: $limit, offset: $offset) {
    total
    items {
      id subject description importance timestamp read
    }
  }
}
"""

_LIST_ARCHIVED = """
query ArchivedNotifications($limit: Int, $offset: Int) {
  archivedNotifications(limit: $limit, offset: $offset) {
    total
    items {
      id subject description importance timestamp
    }
  }
}
"""

_ADD_NOTIFICATION = """
mutation AddNotification($subject: String!, $description: String!, $importance: String) {
  notificationAdd(subject: $subject, description: $description, importance: $importance) {
    success message id
  }
}
"""

_MARK_READ = """
mutation MarkRead($id: String!) {
  notificationMarkRead(id: $id) { success message }
}
"""

_MARK_ALL_READ = """
mutation MarkAllRead {
  notificationMarkAllRead { success message count }
}
"""

_DELETE_NOTIFICATION = """
mutation DeleteNotification($id: String!) {
  notificationDelete(id: $id) { success message }
}
"""

_DELETE_ALL = """
mutation DeleteAllNotifications {
  notificationDeleteAll { success message count }
}
"""

_ARCHIVE_NOTIFICATION = """
mutation ArchiveNotification($id: String!) {
  notificationArchive(id: $id) { success message }
}
"""


async def handle(client: UnraidClient, subaction: str, params: dict[str, Any]) -> Any:
    match subaction:
        case "list":
            return await client.query(
                _LIST_NOTIFICATIONS,
                {"limit": params.get("limit", 50), "offset": params.get("offset", 0)},
                cache=False,
            )
        case "archived":
            return await client.query(
                _LIST_ARCHIVED,
                {"limit": params.get("limit", 50), "offset": params.get("offset", 0)},
                cache=False,
            )
        case "add":
            return await client.mutate(
                _ADD_NOTIFICATION,
                {
                    "subject": params["subject"],
                    "description": params.get("description", ""),
                    "importance": params.get("importance", "normal"),
                },
            )
        case "mark_read":
            return await client.mutate(_MARK_READ, {"id": params["id"]})
        case "mark_all_read":
            return await client.mutate(_MARK_ALL_READ)
        case "delete":
            return await client.mutate(_DELETE_NOTIFICATION, {"id": params["id"]})
        case "delete_all":
            return await client.mutate(_DELETE_ALL)
        case "archive":
            return await client.mutate(_ARCHIVE_NOTIFICATION, {"id": params["id"]})
        case _:
            return {"error": f"Unknown notification subaction: {subaction}"}
