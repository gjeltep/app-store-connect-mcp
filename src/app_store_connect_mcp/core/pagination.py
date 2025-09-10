"""Pagination utilities for App Store Connect API."""

from typing import Dict, Any, Optional, List
from app_store_connect_mcp.core.constants import APP_STORE_CONNECT_MAX_PAGE_SIZE
from app_store_connect_mcp.core.errors import AppStoreConnectError


class PaginationMixin:
    """
    Mixin that provides pagination functionality for API clients.

    This mixin requires the class to have:
    - async get(endpoint, params) method
    - async get_url(url) method
    """

    async def get_all_pages(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = APP_STORE_CONNECT_MAX_PAGE_SIZE,
        max_total: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fetch all pages of a paginated response.

        This is the concrete implementation of the pagination logic that was
        previously embedded in AppStoreConnectAPI. By extracting it to a mixin,
        we make it reusable and testable.

        Args:
            endpoint: API endpoint to fetch
            params: Query parameters
            page_size: Number of items per page (max 200 for App Store Connect)
            max_total: Maximum total items to fetch

        Returns:
            Aggregated response with all data and included resources
        """
        aggregated_data: List[Dict[str, Any]] = []
        aggregated_included: List[Dict[str, Any]] = []

        params = dict(params or {})
        params["limit"] = min(page_size, APP_STORE_CONNECT_MAX_PAGE_SIZE)

        next_url: Optional[str] = None
        page_count = 0

        while True:
            page_count += 1

            # Fetch the page with error handling
            try:
                if next_url:
                    page = await self.get_url(next_url)  # type: ignore
                else:
                    page = await self.get(endpoint, params=params)  # type: ignore
            except Exception as e:
                # Include context about where pagination failed
                raise AppStoreConnectError(
                    f"Pagination failed on page {page_count} while fetching {next_url or endpoint}",
                    details={
                        "page_number": page_count,
                        "endpoint": endpoint,
                        "next_url": next_url,
                        "items_collected": len(aggregated_data),
                        "original_error": str(e),
                    },
                ) from e

            # Extract data and included resources
            data = page.get("data", [])
            included = page.get("included", [])

            if included:
                aggregated_included.extend(included)

            # Handle max_total limit
            if max_total is None:
                aggregated_data.extend(data)
            else:
                remaining = max_total - len(aggregated_data)
                if remaining <= 0:
                    break
                aggregated_data.extend(data[: max(0, remaining)])

            if max_total is not None and len(aggregated_data) >= max_total:
                break

            # Check for next page
            links = page.get("links", {}) or {}
            next_url = links.get("next")
            if not next_url:
                break

        # Build result
        result: Dict[str, Any] = {"data": aggregated_data}
        if aggregated_included:
            result["included"] = aggregated_included
        return result
