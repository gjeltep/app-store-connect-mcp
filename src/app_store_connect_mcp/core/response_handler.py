"""Standardized response handling for API responses."""

from typing import Any


class ResponseHandler:
    """Handler for standardizing API response processing."""

    @staticmethod
    def build_filtered_response(
        filtered_data: list[dict[str, Any]],
        included: list[dict[str, Any]] | None = None,
        endpoint: str = "",
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Build a standardized filtered response.

        Args:
            filtered_data: The filtered data items
            included: Optional included resources
            endpoint: The API endpoint for the self link
            limit: The limit that was applied

        Returns:
            Standardized response dictionary
        """
        response = {
            "data": filtered_data,
            "meta": {
                "paging": {
                    "total": len(filtered_data),
                }
            },
            "links": {"self": endpoint},
        }

        if limit is not None:
            response["meta"]["paging"]["limit"] = limit

        if included:
            response["included"] = included

        return response
