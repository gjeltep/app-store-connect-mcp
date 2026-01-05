"""Users domain handler for MCP tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app_store_connect_mcp.core.base_handler import BaseHandler
from app_store_connect_mcp.domains.users.api_user_invitations import UserInvitationsAPI
from app_store_connect_mcp.domains.users.api_users import UsersAPI

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


class UsersHandler(BaseHandler):
    """MCP tool definitions and handlers for user management."""

    def __init__(self, api):
        """Initialize the handler with API client."""
        super().__init__(api)
        self.users_api = UsersAPI(api)
        self.invitations_api = UserInvitationsAPI(api)

    @staticmethod
    def get_category() -> str:
        """Get the category name for Users tools."""
        return "Users"

    def register_tools(self, mcp: FastMCP) -> None:
        """Register all Users domain tools with the FastMCP server."""

        # User management tools
        @mcp.tool()
        async def users_list(
            filters: dict | None = None,
            sort: str = "username",
            limit: int = 50,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[Users/Management] List all users in the organization.

            Default limit is 50. Max 200. Use pagination metadata for additional pages.
            """
            return await self.users_api.list_users(
                filters=filters, sort=sort, limit=limit, include=include
            )

        @mcp.tool()
        async def users_get(
            user_id: str,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[Users/Management] Get detailed information about a specific user."""
            return await self.users_api.get_user(user_id=user_id, include=include)

        @mcp.tool()
        async def users_modify(
            user_id: str,
            user_data: dict[str, Any],
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[Users/Management] Modify a user account.

            Args:
                user_id: The ID of the user to modify
                user_data: Dictionary containing the fields to update
                include: Optional list of related resources to include

            Returns:
                Updated user information
            """
            return await self.users_api.modify_user(
                user_id=user_id, user_data=user_data, include=include
            )

        @mcp.tool()
        async def users_delete(
            user_id: str,
        ) -> dict[str, Any]:
            """[Users/Management] Remove a user account.

            Args:
                user_id: The ID of the user to delete

            Returns:
                Confirmation of deletion
            """
            return await self.users_api.delete_user(user_id=user_id)

        # User invitation tools
        @mcp.tool()
        async def user_invitations_list(
            filters: dict | None = None,
            sort: str = "email",
            limit: int = 50,
            include: list[str] | None = None,
            visible_apps_limit: int | None = None,
        ) -> dict[str, Any]:
            """[Users/Invitations] List all user invitations.

            Default limit is 50. Max 200. Use pagination metadata for additional pages.
            Supported sort: email, -email, lastName, -lastName
            """
            return await self.invitations_api.list_user_invitations(
                filters=filters,
                sort=sort,
                limit=limit,
                include=include,
                visible_apps_limit=visible_apps_limit,
            )

        @mcp.tool()
        async def user_invitations_get(
            invitation_id: str,
            include: list[str] | None = None,
            visible_apps_limit: int | None = None,
        ) -> dict[str, Any]:
            """[Users/Invitations] Get detailed information about a specific user invitation."""
            return await self.invitations_api.get_user_invitation(
                invitation_id=invitation_id, include=include, visible_apps_limit=visible_apps_limit
            )

        @mcp.tool()
        async def user_invitations_create(
            invitation_data: dict[str, Any],
            include: list[str] | None = None,
            visible_apps_limit: int | None = None,
        ) -> dict[str, Any]:
            """[Users/Invitations] Create a new user invitation.

            Args:
                invitation_data: Dictionary containing the invitation details
                include: Optional list of related resources to include
                visible_apps_limit: Optional limit for visibleApps (1-50)

            Returns:
                Created user invitation information (expires in ~3 days)
            """
            return await self.invitations_api.create_user_invitation(
                invitation_data=invitation_data,
                include=include,
                visible_apps_limit=visible_apps_limit,
            )

        @mcp.tool()
        async def user_invitations_delete(
            invitation_id: str,
        ) -> dict[str, Any]:
            """[Users/Invitations] Cancel/delete a user invitation.

            Args:
                invitation_id: The ID of the invitation to cancel

            Returns:
                Confirmation of cancellation
            """
            return await self.invitations_api.delete_user_invitation(invitation_id=invitation_id)
