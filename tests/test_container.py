"""Tests for dependency injection container."""

import pytest
from unittest.mock import patch, MagicMock
from app_store_connect_mcp.core.container import Container
from app_store_connect_mcp.core.protocols import APIClient, DomainHandler
from tests.mocks import MockAPIClient, MockDomainHandler


class TestContainer:
    """Test dependency injection container."""

    def test_container_creates_api_client(self):
        """Test container creates API client singleton."""
        container = Container()

        # Patch environment variables to avoid configuration errors
        with patch.dict(
            "os.environ",
            {
                "APP_STORE_KEY_ID": "test-key",
                "APP_STORE_ISSUER_ID": "test-issuer",
                "APP_STORE_PRIVATE_KEY_PATH": "/test/path.p8",
            },
        ):
            client1 = container.get_api_client()
            client2 = container.get_api_client()

            # Verify singleton pattern
            assert client1 is client2
            assert isinstance(client1, APIClient)

    @pytest.mark.asyncio
    async def test_container_cleanup(self):
        """Test container cleanup releases resources."""
        container = Container()

        # Create a mock client
        mock_client = MockAPIClient()
        container._api_client = mock_client

        await container.cleanup()
        assert mock_client.is_closed is True


class TestDependencyInjection:
    """Test dependency injection patterns."""

    def test_handlers_use_injected_dependencies(self):
        """Test handlers receive and use injected dependencies."""

        # Create custom container for testing
        class TestContainer(Container):
            def get_domain_handlers(self):
                api = self.get_api_client()
                return [
                    MockDomainHandler(api, "handler1"),
                    MockDomainHandler(api, "handler2"),
                ]

        container = TestContainer()
        mock_client = MockAPIClient()
        container._api_client = mock_client

        handlers = container.get_domain_handlers()
        assert len(handlers) == 2
        assert all(h.api is mock_client for h in handlers)
