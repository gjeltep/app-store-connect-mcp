from __future__ import annotations

from typing import Optional, List, Dict, Any, TYPE_CHECKING

from app_store_connect_mcp.models import (
    BetaFeedbackCrashSubmissionsResponse,
    BetaFeedbackCrashSubmissionResponse,
)

from app_store_connect_mcp.core.base_handler import BaseHandler
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.core.filters import FilterEngine
from app_store_connect_mcp.core.response_handler import ResponseHandler

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

FIELDS_BFCS: List[str] = [
    "createdDate",
    "comment",
    "email",
    "deviceModel",
    "osVersion",
    "locale",
    "timeZone",
    "architecture",
    "connectionType",
    "pairedAppleWatch",
    "appUptimeInMilliseconds",
    "diskBytesAvailable",
    "diskBytesTotal",
    "batteryPercentage",
    "screenWidthInPoints",
    "screenHeightInPoints",
    "appPlatform",
    "devicePlatform",
    "deviceFamily",
    "buildBundleId",
    "crashLog",
    "build",
    "tester",
]

# Mapping from filter keys to API parameter names
CRASH_FILTER_MAPPING = {
    "device_model": "deviceModel",
    "os_version": "osVersion",
    "app_platform": "appPlatform",
    "device_platform": "devicePlatform",
    "build_id": "build",
    "tester_id": "tester",
}


class TestFlightHandler(BaseHandler):
    """MCP tool definitions and handlers for TestFlight crash management."""

    @staticmethod
    def get_category() -> str:
        """Get the category name for TestFlight tools."""
        return "TestFlight"

    def register_tools(self, mcp: "FastMCP") -> None:
        """Register all TestFlight domain tools with the FastMCP server."""

        @mcp.tool()
        async def crashes_list(
            app_id: Optional[str] = None,
            filters: Optional[Dict] = None,
            sort: str = "-createdDate",
            limit: int = 50,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[TestFlight] List crash submissions from beta testers."""
            return await self._get_crash_submissions(
                app_id=app_id, filters=filters, sort=sort, limit=limit, include=include
            )

        @mcp.tool()
        async def crashes_search(
            app_id: Optional[str] = None,
            app_platform: Optional[List[str]] = None,
            device_platform: Optional[List[str]] = None,
            os_min_version: Optional[str] = None,
            os_max_version: Optional[str] = None,
            os_versions: Optional[List[str]] = None,
            device_model: Optional[List[str]] = None,
            device_model_contains: Optional[List[str]] = None,
            created_since_days: Optional[int] = None,
            created_after: Optional[str] = None,
            created_before: Optional[str] = None,
            limit: int = 200,
            include: Optional[List[str]] = None,
            sort: str = "-createdDate",
        ) -> Dict[str, Any]:
            """[TestFlight] Search crash submissions with advanced filtering."""
            return await self._search_crash_submissions(
                app_id=app_id,
                app_platform=app_platform,
                device_platform=device_platform,
                os_min_version=os_min_version,
                os_max_version=os_max_version,
                os_versions=os_versions,
                device_model=device_model,
                device_model_contains=device_model_contains,
                created_since_days=created_since_days,
                created_after=created_after,
                created_before=created_before,
                limit=limit,
                include=include,
                sort=sort,
            )

        @mcp.tool()
        async def crashes_get_by_id(
            submission_id: str,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[TestFlight] Get detailed information about a specific crash submission."""
            return await self._get_crash_submission_details(
                submission_id=submission_id, include=include
            )

        @mcp.tool()
        async def crashes_get_log(
            submission_id: str,
        ) -> Dict[str, Any]:
            """[TestFlight] Get the raw crash log text for a specific crash submission."""
            return await self._get_crash_log(submission_id=submission_id)

    # ----- API calls -----
    async def _get_crash_submissions(
        self,
        app_id: Optional[str] = None,
        filters: Optional[Dict] = None,
        sort: str = "-createdDate",
        limit: int = 50,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get crash submissions for an app."""
        app_id = self.api.ensure_app_id(app_id)
        endpoint = f"/v1/apps/{app_id}/betaFeedbackCrashSubmissions"

        # Build query using the query builder
        query = (
            APIQueryBuilder(endpoint)
            .with_pagination(limit, sort)
            .with_filters(filters, CRASH_FILTER_MAPPING)
            .with_fields("betaFeedbackCrashSubmissions", FIELDS_BFCS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, BetaFeedbackCrashSubmissionsResponse)

    async def _search_crash_submissions(
        self,
        app_id: Optional[str] = None,
        app_platform: Optional[List[str]] = None,
        device_platform: Optional[List[str]] = None,
        os_min_version: Optional[str] = None,
        os_max_version: Optional[str] = None,
        os_versions: Optional[List[str]] = None,
        device_model: Optional[List[str]] = None,
        device_model_contains: Optional[List[str]] = None,
        created_since_days: Optional[int] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: int = 200,
        include: Optional[List[str]] = None,
        sort: str = "-createdDate",
    ) -> Dict[str, Any]:
        """Search crash submissions with advanced filtering."""
        app_id = self.api.ensure_app_id(app_id)
        endpoint = f"/v1/apps/{app_id}/betaFeedbackCrashSubmissions"

        # Build query for server-side filters
        server_filters = {}
        if app_platform:
            server_filters["appPlatform"] = app_platform
        if device_model:
            server_filters["deviceModel"] = device_model
        if os_versions:
            server_filters["osVersion"] = os_versions

        query = (
            APIQueryBuilder(endpoint)
            .with_raw_params({"sort": sort})
            .with_filters(server_filters)  # Direct mapping for these
            .with_fields("betaFeedbackCrashSubmissions", FIELDS_BFCS)
            .with_includes(include)
        )

        # Fetch all data for post-filtering
        raw = await query.execute_all_pages(self.api)
        data = raw.get("data", [])
        included = raw.get("included", [])

        # Build filter pipeline
        filter_engine = FilterEngine(data)

        # Apply device platform filter
        if device_platform:
            filter_engine = filter_engine.filter_by_values(
                "attributes.devicePlatform", device_platform
            )

        # Apply OS version filters
        if os_min_version or os_max_version:
            filter_engine = filter_engine.filter_by_version_range(
                "attributes.osVersion", os_min_version, os_max_version
            )

        # Apply device model substring filter
        if device_model_contains:
            filter_engine = filter_engine.filter_by_text_contains(
                "attributes.deviceModel", device_model_contains
            )

        # Apply date filters
        filter_engine = filter_engine.filter_by_date_range(
            "attributes.createdDate",
            after=created_after,
            before=created_before,
            since_days=created_since_days,
        )

        # Apply limit and get results
        filtered_data = filter_engine.limit(limit).apply()

        # Build standardized response
        return ResponseHandler.build_filtered_response(
            filtered_data=filtered_data,
            included=included if included else None,
            endpoint=endpoint,
            limit=limit,
        )

    async def _get_crash_submission_details(
        self,
        submission_id: str,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get detailed information about a specific crash submission."""
        endpoint = f"/v1/betaFeedbackCrashSubmissions/{submission_id}"

        # Build query
        query = (
            APIQueryBuilder(endpoint)
            .with_fields("betaFeedbackCrashSubmissions", FIELDS_BFCS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, BetaFeedbackCrashSubmissionResponse)

    async def _get_crash_log(self, submission_id: str) -> Dict[str, Any]:
        """Get the raw crash log text for a specific submission."""
        # First get the crash submission with crashLog included
        endpoint = f"/v1/betaFeedbackCrashSubmissions/{submission_id}"

        query = (
            APIQueryBuilder(endpoint)
            .with_includes(["crashLog"])
            .with_raw_params({"fields[betaFeedbackCrashSubmissions]": "crashLog"})
        )

        response = await query.execute(self.api)

        # Extract crash log text from the response
        included = response.get("included", [])
        crash_log_text = None

        for item in included:
            if item.get("type") == "betaFeedbackCrashLogs":
                attributes = item.get("attributes", {})
                crash_log_text = attributes.get("crashLog")
                break

        if crash_log_text:
            return {
                "submission_id": submission_id,
                "crash_log": crash_log_text,
                "status": "success",
            }
        else:
            return {
                "submission_id": submission_id,
                "crash_log": None,
                "status": "not_found",
                "message": "No crash log found for this submission",
            }
