from __future__ import annotations

from typing import Optional, List, Dict, Any, TYPE_CHECKING

from app_store_connect_mcp.models import (
    CustomerReviewsResponse,
    CustomerReviewResponse,
)

from app_store_connect_mcp.core.base_handler import BaseHandler
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.core.filters import FilterEngine
from app_store_connect_mcp.core.response_handler import ResponseHandler

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

FIELDS_CUSTOMER_REVIEWS: List[str] = [
    "rating",
    "title",
    "body",
    "reviewerNickname",
    "createdDate",
    "territory",
]

# Mapping from filter keys to API parameter names
FILTER_MAPPING = {
    "rating": "rating",
    "territory": "territory",
    "appStoreVersion": "appStoreVersion",
}


class AppHandler(BaseHandler):
    """MCP tool definitions and handlers for App Store management."""

    @staticmethod
    def get_category() -> str:
        """Get the category name for App tools."""
        return "App"

    def register_tools(self, mcp: "FastMCP") -> None:
        """Register all App domain tools with the FastMCP server."""

        @mcp.tool()
        async def reviews_list(
            app_id: Optional[str] = None,
            filters: Optional[Dict] = None,
            sort: str = "-createdDate",
            limit: int = 50,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[App] List customer reviews for an app."""
            return await self._list_customer_reviews(
                app_id=app_id, filters=filters, sort=sort, limit=limit, include=include
            )

        @mcp.tool()
        async def reviews_get(
            review_id: str,
            include: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """[App] Get detailed information about a specific customer review."""
            return await self._get_customer_review(review_id=review_id, include=include)

        @mcp.tool()
        async def reviews_search(
            app_id: Optional[str] = None,
            rating: Optional[List[int]] = None,
            min_rating: Optional[int] = None,
            max_rating: Optional[int] = None,
            territory: Optional[List[str]] = None,
            territory_contains: Optional[List[str]] = None,
            created_since_days: Optional[int] = None,
            created_after: Optional[str] = None,
            created_before: Optional[str] = None,
            body_contains: Optional[List[str]] = None,
            title_contains: Optional[List[str]] = None,
            limit: int = 200,
            include: Optional[List[str]] = None,
            sort: str = "-createdDate",
        ) -> Dict[str, Any]:
            """[App] Search customer reviews with advanced filtering."""
            return await self._search_customer_reviews(
                app_id=app_id,
                rating=rating,
                min_rating=min_rating,
                max_rating=max_rating,
                territory=territory,
                territory_contains=territory_contains,
                created_since_days=created_since_days,
                created_after=created_after,
                created_before=created_before,
                body_contains=body_contains,
                title_contains=title_contains,
                limit=limit,
                include=include,
                sort=sort,
            )

    # ----- API calls -----
    async def _list_customer_reviews(
        self,
        app_id: Optional[str] = None,
        filters: Optional[Dict] = None,
        sort: str = "-createdDate",
        limit: int = 50,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """List customer reviews for an app."""
        app_id = self.api.ensure_app_id(app_id)
        endpoint = f"/v1/apps/{app_id}/customerReviews"

        # Build query using the query builder
        query = (
            APIQueryBuilder(endpoint)
            .with_pagination(limit, sort)
            .with_filters(filters, FILTER_MAPPING)
            .with_fields("customerReviews", FIELDS_CUSTOMER_REVIEWS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, CustomerReviewsResponse)

    async def _get_customer_review(
        self,
        review_id: str,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get detailed information about a specific customer review."""
        endpoint = f"/v1/customerReviews/{review_id}"

        # Build query
        query = (
            APIQueryBuilder(endpoint)
            .with_fields("customerReviews", FIELDS_CUSTOMER_REVIEWS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, CustomerReviewResponse)

    async def _search_customer_reviews(
        self,
        app_id: Optional[str] = None,
        rating: Optional[List[int]] = None,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        territory: Optional[List[str]] = None,
        territory_contains: Optional[List[str]] = None,
        created_since_days: Optional[int] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        body_contains: Optional[List[str]] = None,
        title_contains: Optional[List[str]] = None,
        limit: int = 200,
        include: Optional[List[str]] = None,
        sort: str = "-createdDate",
    ) -> Dict[str, Any]:
        """Search customer reviews with advanced filtering."""
        app_id = self.api.ensure_app_id(app_id)
        endpoint = f"/v1/apps/{app_id}/customerReviews"

        # Build query for server-side filters
        server_filters = {}
        if rating:
            server_filters["rating"] = rating
        if territory:
            server_filters["territory"] = territory

        query = (
            APIQueryBuilder(endpoint)
            .with_raw_params({"sort": sort})
            .with_filters(server_filters, FILTER_MAPPING)
            .with_fields("customerReviews", FIELDS_CUSTOMER_REVIEWS)
            .with_includes(include)
        )

        # Fetch all data for post-filtering
        raw = await query.execute_all_pages(self.api)
        data = raw.get("data", [])
        included = raw.get("included", [])

        # Apply post-filters using FilterEngine
        filtered_data = (
            FilterEngine(data)
            .filter_by_numeric_range("attributes.rating", min_rating, max_rating)
            .filter_by_text_contains("attributes.territory", territory_contains)
            .filter_by_date_range(
                "attributes.createdDate",
                after=created_after,
                before=created_before,
                since_days=created_since_days,
            )
            .filter_by_text_contains("attributes.body", body_contains)
            .filter_by_text_contains("attributes.title", title_contains)
            .limit(limit)
            .apply()
        )

        # Build standardized response
        return ResponseHandler.build_filtered_response(
            filtered_data=filtered_data,
            included=included if included else None,
            endpoint=endpoint,
            limit=limit,
        )
