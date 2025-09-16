"""Standardized response handling for API responses."""

from typing import Dict, Any, List, Optional


class ResponseHandler:
    """Handler for standardizing API response processing."""

    @staticmethod
    def build_filtered_response(
        filtered_data: List[Dict[str, Any]],
        included: Optional[List[Dict[str, Any]]] = None,
        endpoint: str = "",
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
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
