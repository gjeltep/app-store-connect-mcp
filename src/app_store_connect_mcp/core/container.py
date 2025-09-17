"""Dependency injection container for the MCP server."""

from typing import List, Optional, TYPE_CHECKING
from app_store_connect_mcp.core.protocols import APIClient, DomainHandler
from app_store_connect_mcp.clients.app_store_connect import AppStoreConnectAPI
from app_store_connect_mcp.domains.testflight import TestFlightHandler
from app_store_connect_mcp.domains.app import AppHandler
from app_store_connect_mcp.domains.analytics import AnalyticsHandler

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


class Container:
    """Dependency injection container."""

    def __init__(self):
        self._api_client: Optional[APIClient] = None
        self._domain_handlers: Optional[List[DomainHandler]] = None

    def get_api_client(self) -> APIClient:
        """Get or create the API client singleton."""
        if self._api_client is None:
            self._api_client = AppStoreConnectAPI()
        return self._api_client

    def get_domain_handlers(self) -> List[DomainHandler]:
        """Get all domain handlers with injected dependencies."""
        if self._domain_handlers is None:
            api = self.get_api_client()
            self._domain_handlers = [
                TestFlightHandler(api),
                AppHandler(api),
                AnalyticsHandler(api),
            ]
        return self._domain_handlers

    def register_all_tools(self, mcp: "FastMCP") -> None:
        """Register all domain tools with the FastMCP server.

        This method iterates through all domain handlers and calls their
        register_tools method to register their tools with the MCP server.

        Args:
            mcp: The FastMCP server instance to register tools with
        """
        for handler in self.get_domain_handlers():
            handler.register_tools(mcp)

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._api_client:
            await self._api_client.aclose()
