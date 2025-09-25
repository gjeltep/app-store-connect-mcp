"""Analytics Reports API operations."""

from typing import Optional, List, Dict, Any

from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.models import (
    AnalyticsReportsResponse,
    AnalyticsReportResponse,
    AnalyticsReportInstancesResponse,
    AnalyticsReportInstanceResponse,
)

# Field definitions
FIELDS_ANALYTICS_REPORTS = ["name", "category"]
FIELDS_ANALYTICS_REPORT_INSTANCES = ["granularity", "processingDate", "segments"]

# Filter mappings
ANALYTICS_FILTER_MAPPING = {
    "granularity": "granularity",
    "processingDate": "processingDate",
    "name": "name",
    "category": "category",
}


class AnalyticsReportsAPI:
    """API operations for analytics reports and instances."""

    def __init__(self, api):
        self.api = api

    async def list_reports_for_request(
        self,
        request_id: str,
        name: Optional[List[str]] = None,
        category: Optional[List[str]] = None,
        limit: int = 50,
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
            .with_limit_and_sort(limit)
            .with_filters(server_filters, ANALYTICS_FILTER_MAPPING)
            .with_fields("analyticsReports", FIELDS_ANALYTICS_REPORTS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportsResponse)

    async def get_report(
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

    async def list_report_instances(
        self,
        report_id: str,
        granularity: Optional[List[str]] = None,
        processing_date: Optional[List[str]] = None,
        limit: int = 100,
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
            .with_limit_and_sort(limit)
            .with_filters(server_filters, ANALYTICS_FILTER_MAPPING)
            .with_fields("analyticsReportInstances", FIELDS_ANALYTICS_REPORT_INSTANCES)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, AnalyticsReportInstancesResponse)

    async def get_report_instance(
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