from __future__ import annotations

from typing import Optional, List, Dict, Any, TYPE_CHECKING

from app_store_connect_mcp.models import (
    AnalyticsReportRequestResponse,
    AnalyticsReportRequestsResponse,
    AnalyticsReportRequestCreateRequest,
    AnalyticsReportsResponse,
    AnalyticsReportResponse,
    AnalyticsReportInstancesResponse,
    AnalyticsReportInstanceResponse,
    AnalyticsReportSegmentsResponse,
    AnalyticsReportSegmentResponse,
)

from app_store_connect_mcp.core.base_handler import BaseHandler
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.core.filters import FilterEngine
from app_store_connect_mcp.core.response_handler import ResponseHandler

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

FIELDS_ANALYTICS_REPORT_REQUESTS: List[str] = [
    "accessType",
    "stoppedDueToInactivity",
    "reports",
]

FIELDS_ANALYTICS_REPORTS: List[str] = [
    "name",
    "category",
    "instances",
]

FIELDS_ANALYTICS_REPORT_INSTANCES: List[str] = [
    "granularity",
    "processingDate",
    "segments",
]

FIELDS_ANALYTICS_REPORT_SEGMENTS: List[str] = [
    "checksum",
    "sizeInBytes",
    "url",
]

# Mapping from filter keys to API parameter names
ANALYTICS_FILTER_MAPPING = {
    "name": "name",
    "category": "category",
    "granularity": "granularity",
    "processing_date": "processingDate",
}


class AnalyticsHandler(BaseHandler):
    """MCP tool definitions and handlers for Analytics reports management."""

    @staticmethod
    def get_category() -> str:
        """Get the category name for Analytics tools."""
        return "Analytics"

    def register_tools(self, mcp: "FastMCP") -> None:
        """Register all Analytics domain tools with the FastMCP server."""

        @mcp.tool()
        async def apps_list_analytics_report_requests(
            app_id: Optional[str] = None,
            access_type: Optional[List[str]] = None,
            limit: int = 200,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics] List analytics report requests for an app."""
            return await self._list_analytics_report_requests_for_app(
                app_id=app_id,
                access_type=access_type,
                limit=limit,
                include=include,
            )

        @mcp.tool()
        async def report_requests_create(
            request_data: Dict[str, Any],
        ) -> Dict[str, Any]:
            """[Analytics] Create a new analytics report request."""
            return await self._create_analytics_report_request(
                request_data=request_data
            )

        @mcp.tool()
        async def report_requests_get(
            request_id: str,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics] Get detailed information about a specific analytics report request."""
            return await self._get_analytics_report_request(
                request_id=request_id, include=include
            )

        @mcp.tool()
        async def report_requests_list_reports(
            request_id: str,
            name: Optional[List[str]] = None,
            category: Optional[List[str]] = None,
            limit: int = 200,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics] List reports for a specific analytics report request."""
            return await self._list_analytics_reports_for_request(
                request_id=request_id,
                name=name,
                category=category,
                limit=limit,
                include=include,
            )

        @mcp.tool()
        async def reports_get(
            report_id: str,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics] Get detailed information about a specific analytics report."""
            return await self._get_analytics_report(
                report_id=report_id, include=include
            )

        @mcp.tool()
        async def reports_list_instances(
            report_id: str,
            granularity: Optional[List[str]] = None,
            processing_date: Optional[List[str]] = None,
            limit: int = 200,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics] List instances for a specific analytics report."""
            return await self._list_analytics_report_instances(
                report_id=report_id,
                granularity=granularity,
                processing_date=processing_date,
                limit=limit,
                include=include,
            )

        @mcp.tool()
        async def report_instances_get(
            instance_id: str,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics] Get detailed information about a specific analytics report instance."""
            return await self._get_analytics_report_instance(
                instance_id=instance_id, include=include
            )

        @mcp.tool()
        async def report_instances_list_segments(
            instance_id: str,
            limit: int = 200,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics] List segments for a specific analytics report instance."""
            return await self._list_analytics_report_instance_segments(
                instance_id=instance_id, limit=limit, include=include
            )

        @mcp.tool()
        async def report_segments_get(
            segment_id: str,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics] Get detailed information about a specific analytics report segment."""
            return await self._get_analytics_report_segment(
                segment_id=segment_id, include=include
            )

    # ----- API calls -----
    async def _get_analytics_report_request(
        self,
        request_id: str,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
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

    async def _list_analytics_reports_for_request(
        self,
        request_id: str,
        name: Optional[List[str]] = None,
        category: Optional[List[str]] = None,
        limit: int = 200,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """List reports for a specific analytics report request."""
        endpoint = f"/v1/analyticsReportRequests/{request_id}/reports"

        # Build query for server-side filters
        server_filters = {}
        if name:
            server_filters["name"] = name
        if category:
            server_filters["category"] = category

        query = (
            APIQueryBuilder(endpoint)
            .with_raw_params({"limit": limit})
            .with_filters(server_filters, ANALYTICS_FILTER_MAPPING)
            .with_fields("analyticsReports", FIELDS_ANALYTICS_REPORTS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportsResponse)

    async def _get_analytics_report(
        self,
        report_id: str,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get detailed information about a specific analytics report."""
        endpoint = f"/v1/analyticsReports/{report_id}"

        # Build query
        query = (
            APIQueryBuilder(endpoint)
            .with_fields("analyticsReports", FIELDS_ANALYTICS_REPORTS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportResponse)

    async def _list_analytics_report_instances(
        self,
        report_id: str,
        granularity: Optional[List[str]] = None,
        processing_date: Optional[List[str]] = None,
        limit: int = 200,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """List instances for a specific analytics report."""
        endpoint = f"/v1/analyticsReports/{report_id}/instances"

        # Build query for server-side filters
        server_filters = {}
        if granularity:
            server_filters["granularity"] = granularity
        if processing_date:
            server_filters["processingDate"] = processing_date

        query = (
            APIQueryBuilder(endpoint)
            .with_raw_params({"limit": limit})
            .with_filters(server_filters, ANALYTICS_FILTER_MAPPING)
            .with_fields("analyticsReportInstances", FIELDS_ANALYTICS_REPORT_INSTANCES)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportInstancesResponse)

    async def _get_analytics_report_instance(
        self,
        instance_id: str,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get detailed information about a specific analytics report instance."""
        endpoint = f"/v1/analyticsReportInstances/{instance_id}"

        # Build query
        query = (
            APIQueryBuilder(endpoint)
            .with_fields("analyticsReportInstances", FIELDS_ANALYTICS_REPORT_INSTANCES)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportInstanceResponse)

    async def _list_analytics_report_instance_segments(
        self,
        instance_id: str,
        limit: int = 200,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """List segments for a specific analytics report instance."""
        endpoint = f"/v1/analyticsReportInstances/{instance_id}/segments"

        # Build query
        query = (
            APIQueryBuilder(endpoint)
            .with_raw_params({"limit": limit})
            .with_fields("analyticsReportSegments", FIELDS_ANALYTICS_REPORT_SEGMENTS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportSegmentsResponse)

    async def _get_analytics_report_segment(
        self,
        segment_id: str,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get detailed information about a specific analytics report segment."""
        endpoint = f"/v1/analyticsReportSegments/{segment_id}"

        # Build query
        query = (
            APIQueryBuilder(endpoint)
            .with_fields("analyticsReportSegments", FIELDS_ANALYTICS_REPORT_SEGMENTS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportSegmentResponse)

    async def _list_analytics_report_requests_for_app(
        self,
        app_id: Optional[str] = None,
        access_type: Optional[List[str]] = None,
        limit: int = 200,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """List analytics report requests for an app."""
        app_id = self.api.ensure_app_id(app_id)
        endpoint = f"/v1/apps/{app_id}/analyticsReportRequests"

        # Build query for server-side filters
        server_filters = {}
        if access_type:
            server_filters["accessType"] = access_type

        query = (
            APIQueryBuilder(endpoint)
            .with_raw_params({"limit": limit})
            .with_filters(server_filters)
            .with_fields("analyticsReportRequests", FIELDS_ANALYTICS_REPORT_REQUESTS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportRequestsResponse)

    async def _create_analytics_report_request(
        self,
        request_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new analytics report request."""
        endpoint = "/v1/analyticsReportRequests"

        # Execute POST request directly with the API client
        response = await self.api.post(endpoint, data=request_data)

        # Return the response data
        return response
