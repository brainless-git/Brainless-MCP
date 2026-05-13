"""User management tools."""

from __future__ import annotations

from typing import Any

from ..core.client import UnraidClient

_LIST_USERS = """
query Users {
  users {
    name description role
  }
}
"""

_ADD_USER = """
mutation AddUser($name: String!, $password: String!, $description: String) {
  userAdd(name: $name, password: $password, description: $description) {
    success message
  }
}
"""

_UPDATE_USER = """
mutation UpdateUser($name: String!, $newPassword: String, $description: String) {
  userEdit(name: $name, newPassword: $newPassword, description: $description) {
    success message
  }
}
"""

_DELETE_USER = """
mutation DeleteUser($name: String!) {
  userDelete(name: $name) { success message }
}
"""

_SET_ROLE = """
mutation SetRole($name: String!, $role: String!) {
  userSetRole(name: $name, role: $role) { success message }
}
"""


async def handle(client: UnraidClient, subaction: str, params: dict[str, Any]) -> Any:
    match subaction:
        case "list":
            return await client.query(_LIST_USERS, cache=True)
        case "add":
            return await client.mutate(
                _ADD_USER,
                {
                    "name": params["name"],
                    "password": params["password"],
                    "description": params.get("description", ""),
                },
                "users",
            )
        case "update":
            return await client.mutate(
                _UPDATE_USER,
                {
                    "name": params["name"],
                    "newPassword": params.get("new_password"),
                    "description": params.get("description"),
                },
                "users",
            )
        case "delete":
            return await client.mutate(_DELETE_USER, {"name": params["name"]}, "users")
        case "set_role":
            return await client.mutate(
                _SET_ROLE, {"name": params["name"], "role": params["role"]}, "users"
            )
        case _:
            return {"error": f"Unknown user subaction: {subaction}"}
