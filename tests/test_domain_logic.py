"""Tests for domain business logic."""

import pytest
from unittest.mock import Mock, AsyncMock
from app_store_connect_mcp.domains.testflight.handlers import TestFlightHandler
from app_store_connect_mcp.domains.app.handlers import AppHandler
from app_store_connect_mcp.core.errors import ValidationError


class TestTestFlightDomainLogic:
    """Test TestFlight domain business logic."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API client."""
        api = Mock()
        api.default_app_id = "test-app-123"
        api.ensure_app_id = Mock(side_effect=lambda x: x or "test-app-123")
        api.get = AsyncMock(return_value={"data": []})
        return api

    @pytest.fixture
    def handler(self, mock_api):
        """Create TestFlight handler with mock API."""
        return TestFlightHandler(mock_api)

    @pytest.mark.asyncio
    async def test_get_crash_submissions_builds_correct_query(self, handler, mock_api):
        """Test that crash submissions query is built correctly."""
        await handler._get_crash_submissions(
            app_id="app-123",
            filters={"deviceModel": ["iPhone14,2"]},
            sort="-createdDate",
            limit=50,
        )

        # Verify API was called with correct endpoint
        mock_api.get.assert_called_once()
        call_args = mock_api.get.call_args
        assert "/v1/apps/app-123/betaFeedbackCrashSubmissions" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_search_crash_submissions_applies_filters(self, handler, mock_api):
        """Test that search applies client-side filters correctly."""
        # Setup mock data - now uses execute() instead of execute_all_pages()
        mock_api.get.return_value = {
            "data": [
                {
                    "id": "1",
                    "attributes": {
                        "devicePlatform": "IOS",
                        "osVersion": "17.0",
                        "createdDate": "2024-01-15T10:00:00Z",
                    },
                },
                {
                    "id": "2",
                    "attributes": {
                        "devicePlatform": "MAC_OS",
                        "osVersion": "16.0",
                        "createdDate": "2024-01-10T10:00:00Z",
                    },
                },
            ]
        }

        result = await handler._search_crash_submissions(
            app_id="app-123", device_platform=["IOS"], os_min_version="17.0"
        )

        # Should filter to only iOS with OS >= 17.0
        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == "1"

    @pytest.mark.asyncio
    async def test_get_crash_log_extracts_text(self, handler, mock_api):
        """Test crash log extraction from response."""
        mock_api.get.return_value = {
            "data": {"type": "betaFeedbackCrashSubmissions"},
            "included": [
                {
                    "type": "betaFeedbackCrashLogs",
                    "attributes": {"crashLog": "Thread 0 crashed..."},
                }
            ],
        }

        result = await handler._get_crash_log("submission-123")

        assert result["status"] == "success"
        assert result["crash_log"] == "Thread 0 crashed..."
        assert result["submission_id"] == "submission-123"


class TestAppDomainLogic:
    """Test App domain business logic."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API client."""
        api = Mock()
        api.default_app_id = "test-app-123"
        api.ensure_app_id = Mock(side_effect=lambda x: x or "test-app-123")
        api.get = AsyncMock(return_value={"data": []})
        return api

    @pytest.fixture
    def handler(self, mock_api):
        """Create App handler with mock API."""
        return AppHandler(mock_api)

    @pytest.mark.asyncio
    async def test_list_customer_reviews_query(self, handler, mock_api):
        """Test customer reviews list query construction."""
        await handler._list_customer_reviews(
            app_id="app-456", filters={"rating": [4, 5]}, sort="-createdDate", limit=100
        )

        # Verify correct endpoint
        call_args = mock_api.get.call_args
        assert "/v1/apps/app-456/customerReviews" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_search_customer_reviews_filters(self, handler, mock_api):
        """Test customer review search with multiple filters."""
        # Now uses execute() instead of execute_all_pages()
        mock_api.get.return_value = {
            "data": [
                {
                    "id": "1",
                    "attributes": {
                        "rating": 5,
                        "title": "Great app",
                        "body": "Love the features",
                        "createdDate": "2024-01-15T10:00:00Z",
                        "territory": "USA",
                    },
                },
                {
                    "id": "2",
                    "attributes": {
                        "rating": 2,
                        "title": "Needs work",
                        "body": "Has bugs",
                        "createdDate": "2024-01-10T10:00:00Z",
                        "territory": "CAN",
                    },
                },
            ]
        }

        result = await handler._search_customer_reviews(
            app_id="app-456", min_rating=4, body_contains=["love"]
        )

        # Should only return 5-star review with "love" in body
        assert len(result["data"]) == 1
        assert result["data"][0]["attributes"]["rating"] == 5
        assert "love" in result["data"][0]["attributes"]["body"].lower()

    @pytest.mark.asyncio
    async def test_get_customer_review_detail(self, handler, mock_api):
        """Test getting detailed review information."""
        mock_api.get.return_value = {
            "data": {
                "id": "review-123",
                "attributes": {"rating": 5, "title": "Excellent"},
            }
        }

        result = await handler._get_customer_review("review-123")

        assert result["data"]["id"] == "review-123"
        assert result["data"]["attributes"]["rating"] == 5


class TestErrorHandling:
    """Test error handling in domain logic."""

    @pytest.mark.asyncio
    async def test_missing_app_id_raises_validation_error(self):
        """Test that missing app_id raises appropriate error."""
        api = Mock()
        api.ensure_app_id = Mock(
            side_effect=ValidationError(
                "app_id is required", user_message="Please provide an app_id"
            )
        )

        handler = TestFlightHandler(api)

        with pytest.raises(ValidationError) as exc_info:
            await handler._get_crash_submissions()

        assert "app_id is required" in str(exc_info.value)
