"""Tests for pagination functionality."""

import pytest
from typing import Dict, Any, Optional
from app_store_connect_mcp.core.pagination import PaginationMixin


class MockPaginatedClient(PaginationMixin):
    """Mock client that implements pagination for testing."""

    def __init__(self, pages: list):
        """Initialize with predefined pages of data."""
        self.pages = pages
        self.current_page = 0
        self.get_url_calls = []
        self.get_calls = []

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return the first page."""
        self.get_calls.append((endpoint, params))
        if self.current_page < len(self.pages):
            page = self.pages[self.current_page]
            self.current_page += 1
            return page
        return {"data": []}

    async def get_url(self, url: str) -> Dict[str, Any]:
        """Return subsequent pages."""
        self.get_url_calls.append(url)
        if self.current_page < len(self.pages):
            page = self.pages[self.current_page]
            self.current_page += 1
            return page
        return {"data": []}


class TestPaginationMixin:
    """Test the PaginationMixin functionality."""

    @pytest.mark.asyncio
    async def test_single_page_response(self):
        """Test handling of single page with no pagination."""
        pages = [{"data": [{"id": "1"}, {"id": "2"}], "links": {}}]

        client = MockPaginatedClient(pages)
        result = await client.get_all_pages("/test")

        assert result == {"data": [{"id": "1"}, {"id": "2"}]}
        assert len(client.get_url_calls) == 0  # No pagination needed

    @pytest.mark.asyncio
    async def test_multiple_pages(self):
        """Test pagination through multiple pages."""
        pages = [
            {
                "data": [{"id": "1"}, {"id": "2"}],
                "links": {"next": "https://api.example.com/page2"},
            },
            {
                "data": [{"id": "3"}, {"id": "4"}],
                "links": {"next": "https://api.example.com/page3"},
            },
            {"data": [{"id": "5"}], "links": {}},
        ]

        client = MockPaginatedClient(pages)
        result = await client.get_all_pages("/test")

        assert len(result["data"]) == 5
        assert result["data"][0]["id"] == "1"
        assert result["data"][4]["id"] == "5"
        assert len(client.get_url_calls) == 2  # Fetched 2 additional pages

    @pytest.mark.asyncio
    async def test_max_total_limit(self):
        """Test that max_total limits items across page boundaries."""
        pages = [
            {
                "data": [{"id": "1"}, {"id": "2"}],
                "links": {"next": "https://api.example.com/page2"},
            },
            {
                "data": [{"id": "3"}, {"id": "4"}],
                "links": {"next": "https://api.example.com/page3"},
            },
        ]

        client = MockPaginatedClient(pages)
        result = await client.get_all_pages("/test", max_total=3)

        # Should stop after getting 3 items even though more are available
        assert len(result["data"]) == 3
        assert result["data"] == [{"id": "1"}, {"id": "2"}, {"id": "3"}]

    @pytest.mark.asyncio
    async def test_included_resources(self):
        """Test aggregation of included resources (App Store Connect pattern)."""
        pages = [
            {
                "data": [{"id": "1", "type": "item"}],
                "included": [{"id": "a", "type": "related"}],
                "links": {"next": "https://api.example.com/page2"},
            },
            {
                "data": [{"id": "2", "type": "item"}],
                "included": [{"id": "b", "type": "related"}],
                "links": {},
            },
        ]

        client = MockPaginatedClient(pages)
        result = await client.get_all_pages("/test")

        assert len(result["data"]) == 2
        assert len(result["included"]) == 2
        assert result["included"][0]["id"] == "a"
        assert result["included"][1]["id"] == "b"
