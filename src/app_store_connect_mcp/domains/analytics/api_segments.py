"""Analytics Report Segments API operations."""

from typing import Any

from app_store_connect_mcp.core.protocols import APIClient
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.models import (
    AnalyticsReportSegmentResponse,
    AnalyticsReportSegmentsResponse,
)

# Field definitions
FIELDS_ANALYTICS_REPORT_SEGMENTS = ["checksum", "sizeInBytes", "url"]


class AnalyticsSegmentsAPI:
    """API operations for analytics report segments."""

    def __init__(self, api: APIClient) -> None:
        self.api = api

    async def list_segments_for_instance(
        self,
        instance_id: str,
        limit: int = 100,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """List segments for a specific analytics report instance."""
        endpoint = f"/v1/analyticsReportInstances/{instance_id}/segments"

        # Build query
        query = (
            APIQueryBuilder(endpoint)
            .with_limit_and_sort(limit)
            .with_fields("analyticsReportSegments", FIELDS_ANALYTICS_REPORT_SEGMENTS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportSegmentsResponse)

    async def get_segment(
        self,
        segment_id: str,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
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
