"""Analytics Report Requests API operations."""

from typing import Any

from app_store_connect_mcp.core.protocols import APIClient
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.models import (
    AnalyticsReportRequestResponse,
    AnalyticsReportRequestsResponse,
)

# Field definitions
FIELDS_ANALYTICS_REPORT_REQUESTS = ["accessType", "stoppedDueToInactivity", "reports"]


class AnalyticsRequestsAPI:
    """API operations for analytics report requests."""

    def __init__(self, api: APIClient) -> None:
        self.api = api

    async def get_report_request(
        self,
        request_id: str,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get detailed information about a specific analytics report request."""
        endpoint = f"/v1/analyticsReportRequests/{request_id}"

        # Build query
        query = (
            APIQueryBuilder(endpoint)
            .with_fields("analyticsReportRequests", FIELDS_ANALYTICS_REPORT_REQUESTS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportRequestResponse)

    async def list_report_requests_for_app(
        self,
        app_id: str | None = None,
        access_type: list[str] | None = None,
        limit: int = 50,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """List analytics report requests for an app."""
        app_id = self.api.ensure_app_id(app_id)
        endpoint = f"/v1/apps/{app_id}/analyticsReportRequests"

        # Build query for server-side filters
        server_filters = {}
        if access_type:
            server_filters["accessType"] = access_type

        query = (
            APIQueryBuilder(endpoint)
            .with_limit_and_sort(limit)
            .with_filters(server_filters)
            .with_fields("analyticsReportRequests", FIELDS_ANALYTICS_REPORT_REQUESTS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportRequestsResponse)

    async def create_report_request(
        self,
        request_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new analytics report request."""
        endpoint = "/v1/analyticsReportRequests"

        # Execute POST request directly with the API client
        response = await self.api.post(endpoint, data=request_data)

        # Return the response data
        return response
