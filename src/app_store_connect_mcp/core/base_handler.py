"""Base handler for domain handlers with FastMCP integration."""

from abc import ABC, abstractmethod
from typing import Optional

from mcp.server.fastmcp import FastMCP
from app_store_connect_mcp.core.protocols import APIClient, DomainHandler
from app_store_connect_mcp.core.errors import ValidationError


class BaseHandler(DomainHandler):
    """Abstract base class for domain handlers that register tools with FastMCP."""

    def __init__(self, api: APIClient):
        """Initialize the handler with an API client.

        Args:
            api: The API client for making requests
        """
        self.api = api

    @abstractmethod
    def register_tools(self, mcp: FastMCP) -> None:
        """Register all tools for this domain with the FastMCP server.

        This method should use @mcp.tool() decorator to register each tool
        function that belongs to this domain.

        Args:
            mcp: The FastMCP server instance to register tools with
        """
        pass
