"""Analytics domain handler for MCP tools."""

from __future__ import annotations

from typing import Optional, List, Dict, Any, TYPE_CHECKING

from app_store_connect_mcp.core.base_handler import BaseHandler
from app_store_connect_mcp.domains.analytics.api_reports import AnalyticsReportsAPI
from app_store_connect_mcp.domains.analytics.api_requests import AnalyticsRequestsAPI
from app_store_connect_mcp.domains.analytics.api_segments import AnalyticsSegmentsAPI

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


class AnalyticsHandler(BaseHandler):
    """Handler for analytics-related MCP tools."""

    def __init__(self, api):
        """Initialize the handler with API client."""
        super().__init__(api)
        self.reports_api = AnalyticsReportsAPI(api)
        self.requests_api = AnalyticsRequestsAPI(api)
        self.segments_api = AnalyticsSegmentsAPI(api)

    def register_tools(self, mcp: FastMCP) -> None:
        """Register analytics-related tools with the MCP server."""

        @mcp.tool()
        async def apps_list_analytics_report_requests(
            app_id: Optional[str] = None,
            access_type: Optional[List[str]] = None,
            limit: int = 50,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics/Requests] List analytics report requests for an app.

            Default limit is 50 to prevent response size issues. Increase limit up to 200 for more results.
            """
            return await self.requests_api.list_report_requests_for_app(
                app_id=app_id,
                access_type=access_type,
                limit=limit,
                include=include,
            )

        @mcp.tool()
        async def report_requests_create(
            request_data: Dict[str, Any],
        ) -> Dict[str, Any]:
            """[Analytics/Requests] Create a new analytics report request."""
            return await self.requests_api.create_report_request(
                request_data=request_data
            )

        @mcp.tool()
        async def report_requests_get(
            request_id: str,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics/Requests] Get detailed information about a specific analytics report request."""
            return await self.requests_api.get_report_request(
                request_id=request_id, include=include
            )

        @mcp.tool()
        async def report_requests_list_reports(
            request_id: str,
            name: Optional[List[str]] = None,
            category: Optional[List[str]] = None,
            limit: int = 50,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics/Reports] List reports for a specific analytics report request.

            Default limit is 50 to prevent response size issues. Increase limit up to 200 for more results.
            """
            return await self.reports_api.list_reports_for_request(
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
            """[Analytics/Reports] Get detailed information about a specific analytics report."""
            return await self.reports_api.get_report(
                report_id=report_id, include=include
            )

        @mcp.tool()
        async def reports_list_instances(
            report_id: str,
            granularity: Optional[List[str]] = None,
            processing_date: Optional[List[str]] = None,
            limit: int = 100,  # Lightweight - mostly IDs/dates
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics/Reports] List instances for a specific analytics report.

            Default limit is 100 (lightweight data). Max 200. Use pagination metadata for additional pages.
            """
            return await self.reports_api.list_report_instances(
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
            """[Analytics/Reports] Get detailed information about a specific analytics report instance."""
            return await self.reports_api.get_report_instance(
                instance_id=instance_id, include=include
            )

        @mcp.tool()
        async def report_instances_list_segments(
            instance_id: str,
            limit: int = 100,  # Lightweight - mostly IDs
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics/Segments] List segments for a specific analytics report instance.

            Default limit is 100 (lightweight data). Max 200. Use pagination metadata for additional pages.
            """
            return await self.segments_api.list_segments_for_instance(
                instance_id=instance_id, limit=limit, include=include
            )

        @mcp.tool()
        async def report_segments_get(
            segment_id: str,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[Analytics/Segments] Get detailed information about a specific analytics report segment."""
            return await self.segments_api.get_segment(
                segment_id=segment_id, include=include
            )