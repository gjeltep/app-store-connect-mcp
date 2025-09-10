"""Mock implementations for testing SOLID architecture."""

from typing import Dict, Any, Optional, List
from mcp.types import Tool, TextContent
from app_store_connect_mcp.core.protocols import APIClient, DomainHandler


class MockAPIClient(APIClient):
    """Mock API client for testing dependency injection."""

    def __init__(self, default_app_id: Optional[str] = "mock-app-123"):
        self._default_app_id = default_app_id
        self.requests = []  # Track requests for assertions
        self.responses = {}  # Pre-configured responses
        self.is_closed = False

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mock GET request."""
        self.requests.append(("GET", endpoint, params))
        return self.responses.get(endpoint, {"data": [], "status": "ok"})

    async def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Mock POST request."""
        self.requests.append(("POST", endpoint, data))
        return self.responses.get(endpoint, {"status": "created"})

    async def delete(self, endpoint: str) -> None:
        """Mock DELETE request."""
        self.requests.append(("DELETE", endpoint, None))

    async def get_url(self, url: str) -> Dict[str, Any]:
        """Mock GET URL."""
        self.requests.append(("GET_URL", url, None))
        return {"data": [], "status": "ok"}

    async def get_all_pages(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 200,
        max_total: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Mock paginated request."""
        self.requests.append(("GET_ALL_PAGES", endpoint, params))
        return self.responses.get(endpoint, {"data": [], "status": "ok"})

    @property
    def default_app_id(self) -> Optional[str]:
        """Mock default app ID."""
        return self._default_app_id

    async def aclose(self) -> None:
        """Mock close."""
        self.is_closed = True


class MockDomainHandler(DomainHandler):
    """Mock domain handler for testing extensibility."""

    def __init__(self, api: APIClient, name: str = "mock"):
        self.api = api
        self.name = name
        self.handled_tools = []

    @staticmethod
    def get_tools() -> List[Tool]:
        """Return mock tools."""
        return [
            Tool(
                name="mock_tool_1",
                description="First mock tool",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="mock_tool_2",
                description="Second mock tool",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    async def handle_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        """Handle mock tool invocation."""
        self.handled_tools.append((name, arguments))

        if name == "mock_tool_1":
            # Demonstrate API usage
            result = await self.api.get("/mock/endpoint")
            return [TextContent(type="text", text=f"Mock result: {result}")]
        elif name == "mock_tool_2":
            return [TextContent(type="text", text="Mock tool 2 executed")]
        else:
            raise ValueError(f"Unknown tool: {name}")


class FailingAPIClient(APIClient):
    """Mock API client that always fails - for error testing."""

    def __init__(self, error_message: str = "API Error"):
        self.error_message = error_message

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        raise Exception(self.error_message)

    async def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        raise Exception(self.error_message)

    async def delete(self, endpoint: str) -> None:
        raise Exception(self.error_message)

    async def get_url(self, url: str) -> Dict[str, Any]:
        raise Exception(self.error_message)

    async def get_all_pages(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 200,
        max_total: Optional[int] = None,
    ) -> Dict[str, Any]:
        raise Exception(self.error_message)

    @property
    def default_app_id(self) -> Optional[str]:
        return None

    async def aclose(self) -> None:
        pass
