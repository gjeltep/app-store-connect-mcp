"""User Invitations API operations."""

from typing import Any

from app_store_connect_mcp.core.protocols import APIClient
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.models import (
    UserInvitationResponse,
    UserInvitationsResponse,
)

# Fields available for user invitation responses
FIELDS_USER_INVITATIONS: list[str] = [
    "email",
    "firstName",
    "lastName",
    "expirationDate",
    "roles",
    "allAppsVisible",
    "provisioningAllowed",
    "visibleApps",
]

# Fields for included apps
FIELDS_APPS: list[str] = [
    "name",
    "bundleId",
]

# Mapping from filter keys to API parameter names
# Valid role values: ADMIN, DEVELOPER, APP_MANAGER, FINANCE, SALES, MARKETING,
# ACCOUNT_HOLDER, ACCESS_TO_REPORTS, CUSTOMER_SUPPORT, CREATE_APPS,
# CLOUD_MANAGED_DEVELOPER_ID, CLOUD_MANAGED_APP_DISTRIBUTION, GENERATE_INDIVIDUAL_KEYS
USER_INVITATION_FILTER_MAPPING = {
    "roles": "roles",
    "email": "email",
    "visibleApps": "visibleApps",
}


class UserInvitationsAPI:
    """API operations for user invitation management."""

    def __init__(self, api: APIClient) -> None:
        self.api = api

    async def list_user_invitations(
        self,
        filters: dict | None = None,
        sort: str = "email",
        limit: int = 50,
        include: list[str] | None = None,
        visible_apps_limit: int | None = None,
    ) -> dict[str, Any]:
        """List all user invitations."""
        endpoint = "/v1/userInvitations"

        # Build query using the query builder
        query = (
            APIQueryBuilder(endpoint)
            .with_limit_and_sort(limit, sort)
            .with_filters(filters, USER_INVITATION_FILTER_MAPPING)
            .with_fields("userInvitations", FIELDS_USER_INVITATIONS)
            .with_includes(include)
        )

        # Add visibleApps limit if include=visibleApps and limit specified
        if include and "visibleApps" in include and visible_apps_limit:
            query = query.with_raw_params({"limit[visibleApps]": visible_apps_limit})

        # Add app fields if including visibleApps
        if include and "visibleApps" in include:
            query = query.with_raw_params({"fields[apps]": ",".join(FIELDS_APPS)})

        # Execute and return
        return await query.execute(self.api, UserInvitationsResponse)

    async def get_user_invitation(
        self,
        invitation_id: str,
        include: list[str] | None = None,
        visible_apps_limit: int | None = None,
    ) -> dict[str, Any]:
        """Get detailed information about a specific user invitation."""
        endpoint = f"/v1/userInvitations/{invitation_id}"

        # Build query
        query = (
            APIQueryBuilder(endpoint)
            .with_fields("userInvitations", FIELDS_USER_INVITATIONS)
            .with_includes(include)
        )

        # Add visibleApps limit if include=visibleApps and limit specified
        if include and "visibleApps" in include and visible_apps_limit:
            query = query.with_raw_params({"limit[visibleApps]": visible_apps_limit})

        # Add app fields if including visibleApps
        if include and "visibleApps" in include:
            query = query.with_raw_params({"fields[apps]": ",".join(FIELDS_APPS)})

        # Execute and return
        return await query.execute(self.api, UserInvitationResponse)

    async def create_user_invitation(
        self,
        invitation_data: dict[str, Any],
        include: list[str] | None = None,
        visible_apps_limit: int | None = None,
    ) -> dict[str, Any]:
        """Create a new user invitation."""
        endpoint = "/v1/userInvitations"

        # Build query for includes
        query = (
            APIQueryBuilder(endpoint)
            .with_fields("userInvitations", FIELDS_USER_INVITATIONS)
            .with_includes(include)
        )

        # Add visibleApps limit if include=visibleApps and limit specified
        if include and "visibleApps" in include and visible_apps_limit:
            query = query.with_raw_params({"limit[visibleApps]": visible_apps_limit})

        # Add app fields if including visibleApps
        if include and "visibleApps" in include:
            query = query.with_raw_params({"fields[apps]": ",".join(FIELDS_APPS)})

        # Execute POST request
        return await self.api.post(endpoint, data=invitation_data, params=query.params)

    async def delete_user_invitation(self, invitation_id: str) -> dict[str, Any]:
        """Cancel/delete a user invitation."""
        endpoint = f"/v1/userInvitations/{invitation_id}"

        # Execute DELETE request
        await self.api.delete(endpoint)

        return {
            "status": "success",
            "message": f"User invitation {invitation_id} has been cancelled",
            "invitation_id": invitation_id,
        }
