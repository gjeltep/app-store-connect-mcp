"""Tests validating SOLID principles in the architecture."""

import pytest
from typing import List
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

            def register_tools(self, mcp) -> None:
                """Register tools with the MCP server."""
                # For this test, we don't need actual registration
                pass

            @staticmethod
            def get_category() -> str:
                """Get the category name."""
                return "NewFeature"

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

    def test_can_swap_implementations_at_runtime(self):
        """Can swap API implementations without changing domain code."""

        # Start with mock client
        mock_client = MockAPIClient()
        handler = MockDomainHandler(mock_client)
        assert handler.api is mock_client

        # Swap to failing client
        failing_client = FailingAPIClient("Network error")
        handler.api = failing_client
        assert handler.api is failing_client

        # Both are valid APIClient implementations
        assert isinstance(handler.api, APIClient)

    def test_container_creates_abstractions(self):
        """Container returns abstractions, not concrete types."""
        container = Container()
        container._api_client = MockAPIClient()

        # Container methods return protocol types
        client = container.get_api_client()
        assert isinstance(client, APIClient)

        handlers = container.get_domain_handlers()
        assert all(isinstance(h, DomainHandler) for h in handlers)
