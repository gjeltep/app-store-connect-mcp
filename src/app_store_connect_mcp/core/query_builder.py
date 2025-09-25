"""Builder pattern for constructing API queries."""

from typing import Dict, Any, List, Optional, Type, TypeVar
from pydantic import BaseModel

from app_store_connect_mcp.core.protocols import APIClient
from app_store_connect_mcp.core.constants import APP_STORE_CONNECT_MAX_PAGE_SIZE

T = TypeVar("T", bound=BaseModel)


class APIQueryBuilder:
    """Fluent interface for building API queries."""

    def __init__(self, endpoint: str):
        """Initialize the query builder.

        Args:
            endpoint: The API endpoint path
        """
        self.endpoint = endpoint
        self.params: Dict[str, Any] = {}

    def with_limit_and_sort(
        self, limit: int, sort: Optional[str] = None
    ) -> "APIQueryBuilder":
        """Add limit and optional sort parameters for MCP pagination.

        This method is designed for MCP server usage where we want predictable
        response sizes without auto-pagination to avoid LLM context overflow.

        Args:
            limit: Maximum number of results (capped at API max of 200)
            sort: Optional sort order for results

        Returns:
            Self for method chaining
        """
        # Cap limit at API maximum to prevent errors
        safe_limit = min(limit, APP_STORE_CONNECT_MAX_PAGE_SIZE)
        self.params["limit"] = safe_limit

        if sort:
            self.params["sort"] = sort

        return self

    def with_filters(
        self,
        filters: Optional[Dict[str, Any]],
        mapping: Optional[Dict[str, str]] = None,
    ) -> "APIQueryBuilder":
        """Add filter parameters with optional key mapping.

        Args:
            filters: Dictionary of filters to apply
            mapping: Optional mapping from filter keys to API parameter names
                    e.g., {"device_model": "deviceModel", "os_version": "osVersion"}

        Returns:
            Self for method chaining
        """
        if not filters:
            return self

        for key, value in filters.items():
            # Map the key if a mapping is provided
            param_key = mapping.get(key, key) if mapping else key

            # Handle list values
            if isinstance(value, list):
                if all(isinstance(v, str) for v in value):
                    self.params[f"filter[{param_key}]"] = ",".join(value)
                else:
                    # Handle non-string lists (e.g., integers)
                    self.params[f"filter[{param_key}]"] = ",".join(
                        str(v) for v in value
                    )
            else:
                self.params[f"filter[{param_key}]"] = value

        return self

    def with_fields(self, resource_type: str, fields: List[str]) -> "APIQueryBuilder":
        """Specify which fields to include in the response.

        Args:
            resource_type: The resource type (e.g., "customerReviews")
            fields: List of field names to include

        Returns:
            Self for method chaining
        """
        if fields:
            self.params[f"fields[{resource_type}]"] = ",".join(fields)
        return self

    def with_includes(self, includes: Optional[List[str]]) -> "APIQueryBuilder":
        """Specify related resources to include.

        Args:
            includes: List of related resources to include

        Returns:
            Self for method chaining
        """
        if includes:
            self.params["include"] = ",".join(includes)
        return self

    def with_raw_params(self, params: Dict[str, Any]) -> "APIQueryBuilder":
        """Add raw parameters directly.

        Args:
            params: Dictionary of parameters to add

        Returns:
            Self for method chaining
        """
        self.params.update(params)
        return self

    async def execute(
        self, api: APIClient, response_model: Optional[Type[T]] = None
    ) -> Dict[str, Any]:
        """Execute the query and optionally parse the response.

        Args:
            api: The API client to use for the request
            response_model: Optional Pydantic model to parse the response

        Returns:
            The API response as a dictionary
        """
        raw = await api.get(self.endpoint, params=self.params)

        # Try to parse with the model if provided
        if response_model:
            try:
                parsed = response_model.model_validate(raw)
                return parsed.model_dump(mode="json")
            except Exception:
                # Return raw response if parsing fails
                return raw

        return raw

