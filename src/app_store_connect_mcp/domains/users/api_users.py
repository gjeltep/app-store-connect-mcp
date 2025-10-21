"""Users API operations."""

from typing import Any

from app_store_connect_mcp.core.protocols import APIClient
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.models import (
    UsersResponse,
    UserResponse,
)

# Fields available for user responses
FIELDS_USERS: list[str] = [
    "username",
    "firstName",
    "lastName",
    "roles",
    "allAppsVisible",
    "provisioningAllowed",
    "visibleApps",
]

# Mapping from filter keys to API parameter names
USER_FILTER_MAPPING = {
    "roles": "roles",
    "username": "username",
    "visibleApps": "visibleApps",
}


class UsersAPI:
    """API operations for user management."""

    def __init__(self, api: APIClient) -> None:
        self.api = api

    async def list_users(
        self,
        filters: dict | None = None,
        sort: str = "username",
        limit: int = 50,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """List all users in the organization."""
        endpoint = "/v1/users"

        # Build query using the query builder
        query = (
            APIQueryBuilder(endpoint)
            .with_limit_and_sort(limit, sort)
            .with_filters(filters, USER_FILTER_MAPPING)
            .with_fields("users", FIELDS_USERS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, UsersResponse)

    async def get_user(
        self,
        user_id: str,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get detailed information about a specific user."""
        endpoint = f"/v1/users/{user_id}"

        # Build query
        query = (
            APIQueryBuilder(endpoint)
            .with_fields("users", FIELDS_USERS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, UserResponse)

    async def modify_user(
        self,
        user_id: str,
        user_data: dict[str, Any],
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Modify a user account."""
        endpoint = f"/v1/users/{user_id}"

        # Build query for includes
        query = (
            APIQueryBuilder(endpoint)
            .with_fields("users", FIELDS_USERS)
            .with_includes(include)
        )

        # Execute PATCH request
        return await self.api.patch(endpoint, data=user_data, params=query.params)

    async def delete_user(self, user_id: str) -> dict[str, Any]:
        """Remove a user account."""
        endpoint = f"/v1/users/{user_id}"

        # Execute DELETE request
        await self.api.delete(endpoint)

        return {
            "status": "success",
            "message": f"User {user_id} has been deleted",
            "user_id": user_id,
        }
