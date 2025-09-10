"""Abstract base classes for dependency inversion."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from mcp.types import Tool, TextContent
from app_store_connect_mcp.core.constants import APP_STORE_CONNECT_MAX_PAGE_SIZE


class APIClient(ABC):
    """Abstract API client interface."""

    @abstractmethod
    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute GET request."""
        pass

    @abstractmethod
    async def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute POST request."""
        pass

    @abstractmethod
    async def delete(self, endpoint: str) -> None:
        """Execute DELETE request."""
        pass

    @abstractmethod
    async def get_url(self, url: str) -> Dict[str, Any]:
        """Get a specific URL."""
        pass

    @abstractmethod
    async def get_all_pages(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = APP_STORE_CONNECT_MAX_PAGE_SIZE,
        max_total: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get all pages of a paginated response."""
        pass

    @property
    @abstractmethod
    def default_app_id(self) -> Optional[str]:
        """Default app ID for operations."""
        pass

    @abstractmethod
    async def aclose(self) -> None:
        """Close the client connection."""
        pass


class DomainHandler(ABC):
    """Abstract domain handler interface."""

    @staticmethod
    @abstractmethod
    def get_tools() -> List[Tool]:
        """Get list of tools this domain provides."""
        pass

    @abstractmethod
    async def handle_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle a tool invocation."""
        pass

    @staticmethod
    def get_category() -> str:
        """Get the category name for this domain's tools."""
        return "General"
