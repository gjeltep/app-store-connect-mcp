"""Tests for core architectural abstractions."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

from app_store_connect_mcp.core.base_handler import BaseHandler
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.core.filters import FilterEngine
from app_store_connect_mcp.core.response_handler import ResponseHandler
from app_store_connect_mcp.core.errors import ValidationError, AppStoreConnectError


class TestBaseHandler:
    """Test the BaseHandler abstract class."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API client."""
        api = Mock()
        api.default_app_id = "test-app-123"
        api.get = AsyncMock()
        return api

    @pytest.fixture
    def test_handler(self, mock_api):
        """Create a concrete test handler."""

        class TestHandler(BaseHandler):
            def register_tools(self, mcp):
                """Register test tools."""
                pass

            async def _test_action(self, param1: str, param2: int = 10):
                return {"result": f"action_{param1}_{param2}"}

            async def _test_other(self):
                return {"result": "other"}

        return TestHandler(mock_api)


class TestAPIQueryBuilder:
    """Test the APIQueryBuilder."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API client."""
        api = Mock()
        api.get = AsyncMock(return_value={"data": []})
        return api

    def test_builder_initialization(self):
        """Test query builder initialization."""
        builder = APIQueryBuilder("/v1/test")
        assert builder.endpoint == "/v1/test"
        assert builder.params == {}


    def test_with_limit_and_sort(self):
        """Test MCP-specific limit and sort method."""
        # Test with limit under max
        builder = APIQueryBuilder("/v1/test").with_limit_and_sort(50, "-createdDate")
        assert builder.params["limit"] == 50
        assert builder.params["sort"] == "-createdDate"

        # Test with limit over max (should cap at 200)
        builder2 = APIQueryBuilder("/v1/test").with_limit_and_sort(500, "rating")
        assert builder2.params["limit"] == 200
        assert builder2.params["sort"] == "rating"

        # Test without sort
        builder3 = APIQueryBuilder("/v1/test").with_limit_and_sort(75)
        assert builder3.params["limit"] == 75
        assert "sort" not in builder3.params

    def test_with_filters(self):
        """Test filter parameters."""
        filters = {"rating": [4, 5], "territory": ["USA", "CAN"]}

        builder = APIQueryBuilder("/v1/test").with_filters(filters)

        assert builder.params["filter[rating]"] == "4,5"
        assert builder.params["filter[territory]"] == "USA,CAN"

    def test_with_filters_mapping(self):
        """Test filter parameters with key mapping."""
        filters = {"device_model": ["iPhone15,1"], "os_version": ["17.0"]}
        mapping = {"device_model": "deviceModel", "os_version": "osVersion"}

        builder = APIQueryBuilder("/v1/test").with_filters(filters, mapping)

        assert builder.params["filter[deviceModel]"] == "iPhone15,1"
        assert builder.params["filter[osVersion]"] == "17.0"

    def test_with_fields(self):
        """Test field selection."""
        builder = APIQueryBuilder("/v1/test").with_fields(
            "reviews", ["rating", "title", "body"]
        )

        assert builder.params["fields[reviews]"] == "rating,title,body"

    def test_with_includes(self):
        """Test include relationships."""
        builder = APIQueryBuilder("/v1/test").with_includes(["response", "author"])

        assert builder.params["include"] == "response,author"

    def test_method_chaining(self):
        """Test fluent interface method chaining."""
        builder = (
            APIQueryBuilder("/v1/test")
            .with_limit_and_sort(100, "-rating")
            .with_filters({"rating": [5]})
            .with_fields("reviews", ["rating"])
            .with_includes(["response"])
        )

        assert builder.endpoint == "/v1/test"
        assert builder.params["sort"] == "-rating"
        assert builder.params["limit"] == 100
        assert builder.params["filter[rating]"] == "5"
        assert builder.params["fields[reviews]"] == "rating"
        assert builder.params["include"] == "response"

    @pytest.mark.asyncio
    async def test_execute(self, mock_api):
        """Test query execution."""
        builder = APIQueryBuilder("/v1/test").with_limit_and_sort(50, "-date")
        result = await builder.execute(mock_api)

        mock_api.get.assert_called_once_with(
            "/v1/test", params={"sort": "-date", "limit": 50}
        )
        assert result == {"data": []}


class TestFilterEngine:
    """Test the FilterEngine."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for filtering."""
        return [
            {
                "id": "1",
                "attributes": {
                    "rating": 5,
                    "title": "Great app",
                    "body": "Love this application",
                    "createdDate": "2024-01-15T10:00:00Z",
                    "territory": "USA",
                    "version": "2.1.0",
                },
            },
            {
                "id": "2",
                "attributes": {
                    "rating": 3,
                    "title": "Okay",
                    "body": "It's fine but has bugs",
                    "createdDate": "2024-01-10T10:00:00Z",
                    "territory": "CAN",
                    "version": "2.0.5",
                },
            },
            {
                "id": "3",
                "attributes": {
                    "rating": 1,
                    "title": "Terrible",
                    "body": "Crashes constantly",
                    "createdDate": "2024-01-20T10:00:00Z",
                    "territory": "GBR",
                    "version": "2.2.0",
                },
            },
        ]

    def test_filter_by_numeric_range(self, sample_data):
        """Test numeric range filtering."""
        engine = FilterEngine(sample_data)
        result = engine.filter_by_numeric_range(
            "attributes.rating", min_value=3, max_value=5
        ).apply()

        assert len(result) == 2
        assert all(3 <= item["attributes"]["rating"] <= 5 for item in result)

    def test_filter_by_text_contains(self, sample_data):
        """Test text contains filtering."""
        engine = FilterEngine(sample_data)
        result = engine.filter_by_text_contains(
            "attributes.body", ["bug", "crash"]
        ).apply()

        assert len(result) == 2
        assert result[0]["id"] == "2"
        assert result[1]["id"] == "3"

    def test_filter_by_text_case_sensitive(self, sample_data):
        """Test case-sensitive text filtering."""
        engine = FilterEngine(sample_data)
        result = engine.filter_by_text_contains(
            "attributes.body", ["Crash"], case_sensitive=True
        ).apply()

        assert len(result) == 1
        assert result[0]["id"] == "3"

    def test_filter_by_values(self, sample_data):
        """Test filtering by exact values."""
        engine = FilterEngine(sample_data)
        result = engine.filter_by_values("attributes.territory", ["USA", "CAN"]).apply()

        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

    def test_filter_by_date_range(self, sample_data):
        """Test date range filtering."""
        engine = FilterEngine(sample_data)
        result = engine.filter_by_date_range(
            "attributes.createdDate",
            after="2024-01-12T00:00:00Z",
            before="2024-01-25T00:00:00Z",
        ).apply()

        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "3"

    def test_filter_by_date_since_days(self, sample_data):
        """Test filtering by days ago."""
        # Mock current time
        with patch("app_store_connect_mcp.core.filters.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 21, tzinfo=timezone.utc)
            mock_datetime.timezone = timezone

            engine = FilterEngine(sample_data)
            result = engine.filter_by_date_range(
                "attributes.createdDate", since_days=7
            ).apply()

            assert len(result) == 2  # Items from last 7 days

    def test_filter_by_version_range(self, sample_data):
        """Test version string filtering."""
        engine = FilterEngine(sample_data)
        result = engine.filter_by_version_range(
            "attributes.version", min_version="2.0.0", max_version="2.1.5"
        ).apply()

        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

    def test_filter_chaining(self, sample_data):
        """Test chaining multiple filters."""
        result = (
            FilterEngine(sample_data)
            .filter_by_numeric_range("attributes.rating", min_value=3)
            .filter_by_text_contains("attributes.body", ["app", "bug"])
            .limit(1)
            .apply()
        )

        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_limit(self, sample_data):
        """Test limiting results."""
        engine = FilterEngine(sample_data)
        result = engine.limit(2).apply()

        assert len(result) == 2


class TestResponseHandler:
    """Test the ResponseHandler."""

    def test_build_filtered_response(self):
        """Test building a standardized filtered response."""
        data = [{"id": "1"}, {"id": "2"}]
        included = [{"type": "related", "id": "r1"}]

        result = ResponseHandler.build_filtered_response(
            filtered_data=data, included=included, endpoint="/v1/test", limit=10
        )

        assert result["data"] == data
        assert result["included"] == included
        assert result["meta"]["paging"]["total"] == 2
        assert result["meta"]["paging"]["limit"] == 10
        assert result["links"]["self"] == "/v1/test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
