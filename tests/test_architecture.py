"""Tests validating SOLID principles in the architecture."""

import pytest
from typing import Dict, Any, List
from mcp.types import Tool, TextContent
from app_store_connect_mcp.core.protocols import APIClient, DomainHandler
from app_store_connect_mcp.core.container import Container
from tests.mocks import MockAPIClient, MockDomainHandler, FailingAPIClient


class TestOpenClosed:
    """Test Open/Closed Principle - open for extension, closed for modification."""

    def test_add_new_domain_without_modifying_existing(self):
        """Can add new domains without changing existing code."""

        # Create a new domain handler without modifying any existing code
        class NewFeatureDomain(DomainHandler):
            def __init__(self, api: APIClient):
                self.api = api

            @staticmethod
            def get_tools() -> List[Tool]:
                return [
                    Tool(
                        name="new_feature",
                        description="New feature tool",
                        inputSchema={"type": "object"},
                    )
                ]

            async def handle_tool(
                self, name: str, arguments: Dict[str, Any]
            ) -> List[TextContent]:
                return [TextContent(type="text", text="New feature executed")]

        # Extend container without modifying it
        class ExtendedContainer(Container):
            def get_domain_handlers(self) -> List[DomainHandler]:
                handlers = super().get_domain_handlers()
                handlers.append(NewFeatureDomain(self.get_api_client()))
                return handlers

        container = ExtendedContainer()
        container._api_client = MockAPIClient()

        handlers = container.get_domain_handlers()
        # Should have original handlers plus new one
        assert len(handlers) >= 2

        # Find our new handler
        new_handler = next(
            (h for h in handlers if isinstance(h, NewFeatureDomain)), None
        )
        assert new_handler is not None


class TestLiskovSubstitution:
    """Test Liskov Substitution Principle - derived classes must be substitutable."""

    @pytest.mark.asyncio
    async def test_mock_client_substitutable_for_api_client(self):
        """MockAPIClient can replace APIClient anywhere."""

        async def use_api_client(client: APIClient):
            """Function that depends on APIClient interface."""
            result = await client.get("/test")
            await client.post("/test", {"data": "value"})
            await client.aclose()
            return result

        # Should work with mock implementation
        mock = MockAPIClient()
        result = await use_api_client(mock)
        assert result == {"data": [], "status": "ok"}
        assert mock.is_closed is True

    @pytest.mark.asyncio
    async def test_handler_substitution(self):
        """Any DomainHandler implementation is substitutable."""

        async def process_tool(handler: DomainHandler, tool_name: str):
            """Function that depends on DomainHandler interface."""
            tools = handler.get_tools()
            if any(t.name == tool_name for t in tools):
                return await handler.handle_tool(tool_name, {})
            return None

        # Should work with any handler implementation
        mock_handler = MockDomainHandler(MockAPIClient())
        result = await process_tool(mock_handler, "mock_tool_1")
        assert result is not None


class TestDependencyInversion:
    """Test Dependency Inversion - depend on abstractions, not concretions."""

    def test_handlers_depend_on_abstraction(self):
        """Handlers depend on APIClient interface, not concrete implementation."""

        # Handler accepts any APIClient implementation
        mock_client = MockAPIClient()
        failing_client = FailingAPIClient()

        handler1 = MockDomainHandler(mock_client)
        handler2 = MockDomainHandler(failing_client)

        assert handler1.api is mock_client
        assert handler2.api is failing_client

        # Both are valid because they implement APIClient
        assert isinstance(handler1.api, APIClient)
        assert isinstance(handler2.api, APIClient)

    @pytest.mark.asyncio
    async def test_can_swap_implementations_at_runtime(self):
        """Can swap API implementations without changing domain code."""

        # Start with mock client
        mock_client = MockAPIClient()
        handler = MockDomainHandler(mock_client)

        result = await handler.handle_tool("mock_tool_1", {})
        assert "Mock result" in result[0].text

        # Swap to failing client
        handler.api = FailingAPIClient("Network error")

        with pytest.raises(Exception, match="Network error"):
            await handler.handle_tool("mock_tool_1", {})

    def test_container_creates_abstractions(self):
        """Container returns abstractions, not concrete types."""
        container = Container()
        container._api_client = MockAPIClient()

        # Container methods return protocol types
        client = container.get_api_client()
        assert isinstance(client, APIClient)

        handlers = container.get_domain_handlers()
        assert all(isinstance(h, DomainHandler) for h in handlers)


class TestArchitectureExtensibility:
    """Test that architecture supports unlimited extension."""

    @pytest.mark.asyncio
    async def test_multiple_domains_coexist(self):
        """Multiple domain handlers can work together."""

        api = MockAPIClient()

        # Create multiple different domains
        handler1 = MockDomainHandler(api, "domain1")
        handler2 = MockDomainHandler(api, "domain2")

        # Build tool registry like server does
        tool_registry = {}
        for handler in [handler1, handler2]:
            for tool in handler.get_tools():
                tool_registry[tool.name] = handler

        # All tools are registered
        assert "mock_tool_1" in tool_registry
        assert "mock_tool_2" in tool_registry

        # Can invoke tools from different handlers
        result1 = await tool_registry["mock_tool_1"].handle_tool("mock_tool_1", {})
        result2 = await tool_registry["mock_tool_2"].handle_tool("mock_tool_2", {})

        assert result1 is not None
        assert result2 is not None
