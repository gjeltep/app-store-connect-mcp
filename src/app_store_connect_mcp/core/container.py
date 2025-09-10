"""Dependency injection container for the MCP server."""

from typing import List, Optional
from app_store_connect_mcp.core.protocols import APIClient, DomainHandler
from app_store_connect_mcp.clients.app_store_connect import AppStoreConnectAPI
from app_store_connect_mcp.domains.testflight import TestFlightHandler


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
                # Add new domain handlers here
            ]
        return self._domain_handlers

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._api_client:
            await self._api_client.aclose()
