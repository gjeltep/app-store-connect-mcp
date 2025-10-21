"""Abstract base classes for dependency inversion."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

# Avoid circular import - FastMCP only needed for type hints, not runtime
if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


class APIClient(ABC):
    """Abstract API client interface."""

    @abstractmethod
    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute GET request."""
        pass

    @abstractmethod
    async def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute POST request."""
        pass

    @abstractmethod
    async def patch(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute PATCH request."""
        pass

    @abstractmethod
    async def delete(self, endpoint: str) -> None:
        """Execute DELETE request."""
        pass

    @abstractmethod
    async def get_url(self, url: str) -> dict[str, Any]:
        """Get a specific URL."""
        pass

    @property
    @abstractmethod
    def default_app_id(self) -> str | None:
        """Default app ID for operations."""
        pass

    @abstractmethod
    def ensure_app_id(self, app_id: str | None) -> str:
        """Ensure we have a valid app_id, using the default if needed.

        Args:
            app_id: The provided app_id or None

        Returns:
            The app_id to use

        Raises:
            ValidationError: If no app_id is provided and no default is set
        """
        pass

    @abstractmethod
    async def aclose(self) -> None:
        """Close the client connection."""
        pass


class DomainHandler(ABC):
    """Abstract domain handler interface."""

    @abstractmethod
    def register_tools(self, mcp: "FastMCP") -> None:
        """Register all tools for this domain with the FastMCP server.

        This method should use @mcp.tool() decorator to register each tool
        function that belongs to this domain.

        Args:
            mcp: The FastMCP server instance to register tools with
        """
        pass

    @staticmethod
    def get_category() -> str:
        """Get the category name for this domain's tools."""
        return "General"
