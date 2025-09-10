"""Tests for abstract protocol validation."""

import pytest
from app_store_connect_mcp.core.protocols import APIClient, DomainHandler
from app_store_connect_mcp.clients.app_store_connect import AppStoreConnectAPI
from app_store_connect_mcp.domains.testflight.handlers import TestFlightHandler
from tests.mocks import MockAPIClient, MockDomainHandler


class TestAPIClientProtocol:
    """Test APIClient abstract base class."""

    def test_cannot_instantiate_abstract_client(self):
        """Verify APIClient cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            APIClient()

    def test_mock_client_implements_protocol(self):
        """Verify MockAPIClient properly implements APIClient."""
        client = MockAPIClient()
        assert isinstance(client, APIClient)

    @pytest.mark.asyncio
    async def test_mock_client_has_all_methods(self):
        """Verify mock has all required methods."""
        client = MockAPIClient()

        # Test all abstract methods exist and work
        result = await client.get("/test")
        assert result == {"data": [], "status": "ok"}

        result = await client.post("/test", {"key": "value"})
        assert result == {"status": "created"}

        await client.delete("/test")

        result = await client.get_url("http://test.com")
        assert result == {"data": [], "status": "ok"}

        result = await client.get_all_pages("/test")
        assert result == {"data": [], "status": "ok"}

        assert client.default_app_id == "mock-app-123"

        await client.aclose()
        assert client.is_closed is True


class TestDomainHandlerProtocol:
    """Test DomainHandler abstract base class."""

    def test_cannot_instantiate_abstract_handler(self):
        """Verify DomainHandler cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            DomainHandler()

    def test_mock_handler_implements_protocol(self):
        """Verify MockDomainHandler properly implements DomainHandler."""
        api = MockAPIClient()
        handler = MockDomainHandler(api)
        assert isinstance(handler, DomainHandler)

    def test_handler_has_required_methods(self):
        """Verify handler has all required methods."""
        api = MockAPIClient()
        handler = MockDomainHandler(api)

        tools = handler.get_tools()
        assert len(tools) == 2
        assert tools[0].name == "mock_tool_1"

    @pytest.mark.asyncio
    async def test_handler_tool_invocation(self):
        """Test handler can handle tool invocations."""
        api = MockAPIClient()
        handler = MockDomainHandler(api)

        result = await handler.handle_tool("mock_tool_1", {})
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Mock result" in result[0].text


class TestConcreteImplementations:
    """Test that concrete implementations satisfy protocols."""

    def test_testflight_implements_handler(self):
        """Verify TestFlightHandler implements DomainHandler."""
        api = MockAPIClient()
        handler = TestFlightHandler(api)
        assert isinstance(handler, DomainHandler)

    def test_testflight_has_tools(self):
        """Verify TestFlightHandler provides tools."""
        tools = TestFlightHandler.get_tools()
        assert len(tools) > 0
        assert all(hasattr(tool, "name") for tool in tools)
        assert all(hasattr(tool, "description") for tool in tools)
