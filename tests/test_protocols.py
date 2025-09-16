"""Tests for abstract protocol validation."""

import pytest
from app_store_connect_mcp.core.protocols import APIClient, DomainHandler
from app_store_connect_mcp.clients.app_store_connect import AppStoreConnectAPI
from app_store_connect_mcp.domains.testflight.handlers import TestFlightHandler
from app_store_connect_mcp.domains.app.handlers import AppHandler
from tests.mocks import MockAPIClient, MockDomainHandler


class TestAPIClientProtocol:
    """Test APIClient protocol implementation."""

    @pytest.mark.asyncio
    async def test_api_client_lifecycle(self):
        """Test API client can be created and closed properly."""
        client = MockAPIClient()
        assert isinstance(client, APIClient)
        assert client.default_app_id == "mock-app-123"

        # Test client can be closed
        await client.aclose()
        assert client.is_closed is True


class TestDomainHandlerProtocol:
    """Test DomainHandler protocol implementation."""

    def test_handler_stores_api_client(self):
        """Verify handler stores and uses API client."""
        api = MockAPIClient()
        handler = MockDomainHandler(api)
        assert handler.api is api
        assert isinstance(handler, DomainHandler)


class TestConcreteImplementations:
    """Test concrete handler implementations."""

    def test_handler_categories(self):
        """Verify handlers provide correct categories."""
        assert TestFlightHandler.get_category() == "TestFlight"
        assert AppHandler.get_category() == "App"
