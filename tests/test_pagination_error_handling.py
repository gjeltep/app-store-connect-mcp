"""Test error handling in pagination."""

import pytest
from typing import Dict, Any, Optional
from app_store_connect_mcp.core.pagination import PaginationMixin
from app_store_connect_mcp.core.errors import AppStoreConnectError


class FailingPaginatedClient(PaginationMixin):
    """Mock client that fails during pagination."""

    def __init__(self):
        """Initialize the failing client."""
        self.call_count = 0

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return first page successfully."""
        self.call_count += 1
        return {
            "data": [{"id": "1"}, {"id": "2"}],
            "links": {"next": "https://api.example.com/page2"},
        }

    async def get_url(self, url: str) -> Dict[str, Any]:
        """Fail on second page to test error handling."""
        self.call_count += 1
        raise ConnectionError("Network error during pagination")


class TestPaginationErrorHandling:
    """Test error handling in pagination."""

    @pytest.mark.asyncio
    async def test_pagination_error_includes_context(self):
        """Test that pagination errors include debugging context."""
        client = FailingPaginatedClient()

        with pytest.raises(AppStoreConnectError) as exc_info:
            await client.get_all_pages("/test/endpoint")

        # Verify error was wrapped with context
        error = exc_info.value
        assert "Pagination failed" in str(error)
        assert error.details["endpoint"] == "/test/endpoint"
        assert error.details["items_collected"] == 2  # Got first page before failure
        assert "Network error" in error.details["original_error"]
