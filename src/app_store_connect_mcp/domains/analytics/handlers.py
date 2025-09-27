"""Analytics domain handler for MCP tools."""

from __future__ import annotations

from typing import Optional, List, Dict, Any, TYPE_CHECKING

from app_store_connect_mcp.core.base_handler import BaseHandler
from app_store_connect_mcp.domains.analytics.api_reports import AnalyticsReportsAPI
from app_store_connect_mcp.domains.analytics.api_requests import AnalyticsRequestsAPI
from app_store_connect_mcp.domains.analytics.api_segments import AnalyticsSegmentsAPI
from app_store_connect_mcp.domains.analytics.data_downloader import (
    AnalyticsDataDownloader,
)

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
        self.data_downloader = AnalyticsDataDownloader()

    def register_tools(self, mcp: FastMCP) -> None:
        """Register analytics-related tools with the MCP server."""

        @mcp.tool()
        async def analytics_report_requests_list(
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
            limit: int = 100,
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

        @mcp.tool()
        async def report_instances_download_data(
            instance_id: str,
            output_path: Optional[str] = None,
        ) -> Dict[str, Any]:
            """[Analytics/Data] Download analytics report data to a TSV file.

            This tool fetches all segments for a report instance and saves the data to a TSV file.
            The file can then be analyzed using other tools.

            Args:
                instance_id: The analytics report instance ID
                output_path: Optional path for the output file. If not provided, saves to temp directory

            Returns:
                Dict containing:
                - status: "success", "no_data", or "error"
                - file_path: Path to the downloaded TSV file
                - file_size_mb: File size in megabytes
                - segment_count: Number of segments downloaded
                - row_count: Number of data rows (excluding header)
                - message: Error message if status is "error" or "no_data"
            """
            try:
                # Get all segments for this instance
                segments_response = await self.segments_api.list_segments_for_instance(
                    instance_id=instance_id,
                    limit=200,  # Get all segments
                )

                segments = segments_response.get("data", [])

                # Download segments to file
                result = await self.data_downloader.download_segments_to_file(
                    segments=segments, output_path=output_path
                )

                return result

            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to download report data: {str(e)}",
                    "file_path": None,
                    "file_size_mb": 0,
                    "segment_count": 0,
                    "row_count": 0,
                }

    async def cleanup(self) -> None:
        """Cleanup resources when handler is destroyed."""
        if hasattr(self, "data_downloader"):
            await self.data_downloader.aclose()
