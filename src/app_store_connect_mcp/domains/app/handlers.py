from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app_store_connect_mcp.core.base_handler import BaseHandler
from app_store_connect_mcp.core.filters import FilterEngine
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.core.response_handler import ResponseHandler
from app_store_connect_mcp.models import (
    CustomerReviewResponse,
    CustomerReviewsResponse,
)

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

FIELDS_CUSTOMER_REVIEWS: list[str] = [
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

    def register_tools(self, mcp: FastMCP) -> None:
        """Register all App domain tools with the FastMCP server."""

        @mcp.tool()
        async def reviews_list(
            app_id: str | None = None,
            filters: dict | None = None,
            sort: str = "-createdDate",
            limit: int = 50,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[App] List customer reviews for an app."""
            return await self._list_customer_reviews(
                app_id=app_id, filters=filters, sort=sort, limit=limit, include=include
            )

        @mcp.tool()
        async def reviews_get(
            review_id: str,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[App] Get detailed information about a specific customer review."""
            return await self._get_customer_review(review_id=review_id, include=include)

        @mcp.tool()
        async def reviews_search(
            app_id: str | None = None,
            rating: list[int] | None = None,
            min_rating: int | None = None,
            max_rating: int | None = None,
            territory: list[str] | None = None,
            territory_contains: list[str] | None = None,
            created_since_days: int | None = None,
            created_after: str | None = None,
            created_before: str | None = None,
            body_contains: list[str] | None = None,
            title_contains: list[str] | None = None,
            limit: int = 50,
            include: list[str] | None = None,
            sort: str = "-createdDate",
        ) -> dict[str, Any]:
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
        app_id: str | None = None,
        filters: dict | None = None,
        sort: str = "-createdDate",
        limit: int = 50,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """List customer reviews for an app."""
        app_id = self.api.ensure_app_id(app_id)
        endpoint = f"/v1/apps/{app_id}/customerReviews"

        # Build query using the query builder
        query = (
            APIQueryBuilder(endpoint)
            .with_limit_and_sort(limit, sort)
            .with_filters(filters, FILTER_MAPPING)
            .with_fields("customerReviews", FIELDS_CUSTOMER_REVIEWS)
            .with_includes(include)
        )

        # Execute and return
        return await query.execute(self.api, CustomerReviewsResponse)

    async def _get_customer_review(
        self,
        review_id: str,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
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
        app_id: str | None = None,
        rating: list[int] | None = None,
        min_rating: int | None = None,
        max_rating: int | None = None,
        territory: list[str] | None = None,
        territory_contains: list[str] | None = None,
        created_since_days: int | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        body_contains: list[str] | None = None,
        title_contains: list[str] | None = None,
        limit: int = 50,
        include: list[str] | None = None,
        sort: str = "-createdDate",
    ) -> dict[str, Any]:
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
            .with_limit_and_sort(limit, sort)
            .with_filters(server_filters, FILTER_MAPPING)
            .with_fields("customerReviews", FIELDS_CUSTOMER_REVIEWS)
            .with_includes(include)
        )

        # Execute query without auto-pagination
        raw = await query.execute(self.api)
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
