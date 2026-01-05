"""Tests for Xcode Cloud helper functions and query construction patterns."""

from unittest.mock import AsyncMock

import pytest

from app_store_connect_mcp.core.errors import ResourceNotFoundError, ValidationError
from app_store_connect_mcp.domains.xcode_cloud.api_builds import (
    _fetch_action_resources,
    _resolve_git_reference_id,
    list_builds,
    start_build,
    start_build_by_ref_id,
)


class TestXcodeCloudQueryConstruction:
    """Test query construction patterns in Xcode Cloud domain."""

    @pytest.mark.asyncio
    async def test_list_builds_with_workflow_id(self):
        """Test that list_builds constructs correct query for workflow."""
        mock_api = AsyncMock()
        mock_api.get = AsyncMock(return_value={"data": [], "meta": {"paging": {"total": 0}}})

        await list_builds(api=mock_api, workflow_id="test-workflow-123", limit=10)

        # Verify the endpoint was constructed correctly
        mock_api.get.assert_called_once()
        args = mock_api.get.call_args[0]
        assert "/v1/ciWorkflows/test-workflow-123/buildRuns" in args[0]

        # Verify query parameters were added
        kwargs = mock_api.get.call_args[1]
        params = kwargs.get("params", {})
        assert params["limit"] == 10
        assert params["sort"] == "-number"
        assert "fields[ciBuildRuns]" in params

    @pytest.mark.asyncio
    async def test_list_builds_raises_validation_error(self):
        """Test that list_builds raises ValidationError when neither ID is provided."""
        mock_api = AsyncMock()

        with pytest.raises(ValidationError) as exc_info:
            await list_builds(api=mock_api)

        assert "either product_id or workflow_id must be provided" in str(exc_info.value)
        assert exc_info.value.category.value == "validation"

    @pytest.mark.asyncio
    async def test_list_builds_single_query_construction(self):
        """Test that query building logic is not duplicated between workflow and product paths."""
        mock_api = AsyncMock()
        mock_api.get = AsyncMock(return_value={"data": [], "meta": {"paging": {"total": 0}}})

        # Test with workflow
        await list_builds(api=mock_api, workflow_id="w1", filters={"is_pull_request_build": True})
        call1_params = mock_api.get.call_args[1]["params"]

        # Test with product
        await list_builds(api=mock_api, product_id="p1", filters={"is_pull_request_build": True})
        call2_params = mock_api.get.call_args[1]["params"]

        # Both should have identical query parameters
        assert call1_params == call2_params


class TestFetchActionResources:
    """Test the DRY helper for fetching resources from build actions."""

    @pytest.mark.asyncio
    async def test_fetch_action_resources_basic(self):
        """Test basic resource fetching pattern with action context."""
        mock_api = AsyncMock()

        # Mock the actions response
        mock_api.get = AsyncMock(
            side_effect=[
                # First call: get actions
                {
                    "data": [
                        {
                            "id": "action-1",
                            "attributes": {"name": "Build", "actionType": "BUILD"},
                        },
                        {
                            "id": "action-2",
                            "attributes": {"name": "Test", "actionType": "TEST"},
                        },
                    ],
                    "meta": {"paging": {"total": 2}},
                },
                # Second call: get resources for action-1
                {
                    "data": [{"id": "artifact-1", "type": "ciArtifacts"}],
                    "meta": {"paging": {"total": 1}},
                },
                # Third call: get resources for action-2
                {
                    "data": [{"id": "artifact-2", "type": "ciArtifacts"}],
                    "meta": {"paging": {"total": 1}},
                },
            ]
        )

        result = await _fetch_action_resources(
            api=mock_api,
            build_id="build-123",
            resource_endpoint_suffix="artifacts",
            resource_fields_name="ciArtifacts",
            resource_fields=["fileType", "fileName"],
            action_fields=["name", "actionType"],
            limit=50,
        )

        # Verify structure
        assert "data" in result
        assert "meta" in result
        assert result["meta"]["total"] == 2

        # Verify action context was added
        for resource in result["data"]:
            assert "_action" in resource
            assert "id" in resource["_action"]
            assert "name" in resource["_action"]
            assert "actionType" in resource["_action"]

    @pytest.mark.asyncio
    async def test_fetch_action_resources_with_filter(self):
        """Test resource fetching with action filtering."""
        mock_api = AsyncMock()

        # Mock the actions response with mixed action types
        mock_api.get = AsyncMock(
            side_effect=[
                # First call: get actions
                {
                    "data": [
                        {
                            "id": "action-1",
                            "attributes": {"name": "Build", "actionType": "BUILD"},
                        },
                        {
                            "id": "action-2",
                            "attributes": {"name": "Test", "actionType": "TEST"},
                        },
                        {
                            "id": "action-3",
                            "attributes": {"name": "Archive", "actionType": "ARCHIVE"},
                        },
                    ],
                    "meta": {"paging": {"total": 3}},
                },
                # Second call: get resources for TEST action only
                {
                    "data": [{"id": "test-result-1", "type": "ciTestResults"}],
                    "meta": {"paging": {"total": 1}},
                },
            ]
        )

        # Filter to only TEST actions
        def is_test_action(action):
            action_type = action.get("attributes", {}).get("actionType")
            return action_type and "TEST" in str(action_type).upper()

        result = await _fetch_action_resources(
            api=mock_api,
            build_id="build-456",
            resource_endpoint_suffix="testResults",
            resource_fields_name="ciTestResults",
            resource_fields=["status", "name"],
            action_fields=["name", "actionType"],
            limit=100,
            filter_actions=is_test_action,
        )

        # Should only fetch resources for TEST action
        assert mock_api.get.call_count == 2  # actions + 1 test action
        assert result["meta"]["total"] == 1

        # Verify the correct endpoint was called
        second_call_args = mock_api.get.call_args_list[1][0]
        assert "action-2/testResults" in second_call_args[0]

    @pytest.mark.asyncio
    async def test_fetch_action_resources_handles_empty_actions(self):
        """Test resource fetching handles builds with no actions gracefully."""
        mock_api = AsyncMock()
        mock_api.get = AsyncMock(return_value={"data": [], "meta": {"paging": {"total": 0}}})

        result = await _fetch_action_resources(
            api=mock_api,
            build_id="build-789",
            resource_endpoint_suffix="issues",
            resource_fields_name="ciIssues",
            resource_fields=["issueType", "message"],
            action_fields=["name", "actionType"],
            limit=50,
        )

        assert result["data"] == []
        assert result["meta"]["total"] == 0
        assert mock_api.get.call_count == 1  # Only the actions call


class TestGitReferenceResolution:
    """Test git reference name to UUID resolution."""

    @pytest.mark.asyncio
    async def test_resolve_branch_name_success(self):
        """Test successful branch name resolution."""
        mock_api = AsyncMock()

        mock_api.get = AsyncMock(
            side_effect=[
                # First call: get workflow with repository
                {
                    "data": {
                        "id": "workflow-123",
                        "type": "ciWorkflows",
                        "relationships": {
                            "repository": {"data": {"type": "scmRepositories", "id": "repo-456"}}
                        },
                    }
                },
                # Second call: list git references
                {
                    "data": [
                        {
                            "id": "ref-uuid-main",
                            "type": "scmGitReferences",
                            "attributes": {
                                "name": "main",
                                "canonicalName": "refs/heads/main",
                                "isDeleted": False,
                                "kind": "BRANCH",
                            },
                        },
                        {
                            "id": "ref-uuid-develop",
                            "type": "scmGitReferences",
                            "attributes": {
                                "name": "develop",
                                "canonicalName": "refs/heads/develop",
                                "isDeleted": False,
                                "kind": "BRANCH",
                            },
                        },
                    ]
                },
            ]
        )

        result = await _resolve_git_reference_id(
            api=mock_api,
            workflow_id="workflow-123",
            branch_or_tag_name="main",
        )

        assert result == "ref-uuid-main"

    @pytest.mark.asyncio
    async def test_resolve_deleted_branch_raises_error(self):
        """Test that deleted branches raise ResourceNotFoundError."""
        mock_api = AsyncMock()

        mock_api.get = AsyncMock(
            side_effect=[
                {"data": {"relationships": {"repository": {"data": {"id": "repo-456"}}}}},
                {
                    "data": [
                        {
                            "id": "ref-uuid-deleted",
                            "attributes": {
                                "name": "old-branch",
                                "isDeleted": True,
                            },
                        },
                    ]
                },
            ]
        )

        with pytest.raises(ResourceNotFoundError) as exc_info:
            await _resolve_git_reference_id(
                api=mock_api,
                workflow_id="workflow-123",
                branch_or_tag_name="old-branch",
            )

        assert "has been deleted" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resolve_nonexistent_branch_raises_error(self):
        """Test that non-existent branches raise ResourceNotFoundError."""
        mock_api = AsyncMock()

        mock_api.get = AsyncMock(
            side_effect=[
                {"data": {"relationships": {"repository": {"data": {"id": "repo-456"}}}}},
                {
                    "data": [
                        {
                            "id": "ref-uuid-main",
                            "attributes": {"name": "main", "isDeleted": False},
                        },
                    ]
                },
            ]
        )

        with pytest.raises(ResourceNotFoundError) as exc_info:
            await _resolve_git_reference_id(
                api=mock_api,
                workflow_id="workflow-123",
                branch_or_tag_name="nonexistent-branch",
            )

        assert "not found" in str(exc_info.value)
        assert "main" in str(exc_info.value.details.get("available_references", []))

    @pytest.mark.asyncio
    async def test_resolve_no_repository_raises_error(self):
        """Test that workflows without repositories raise ValidationError."""
        mock_api = AsyncMock()

        mock_api.get = AsyncMock(
            return_value={
                "data": {
                    "id": "workflow-123",
                    "relationships": {},  # No repository
                }
            }
        )

        with pytest.raises(ValidationError) as exc_info:
            await _resolve_git_reference_id(
                api=mock_api,
                workflow_id="workflow-123",
                branch_or_tag_name="main",
            )

        assert "no associated repository" in str(exc_info.value)


class TestStartBuildWithResolution:
    """Test start_build function with branch name resolution."""

    @pytest.mark.asyncio
    async def test_start_build_resolves_branch_name(self):
        """Test that start_build resolves branch names via API."""
        mock_api = AsyncMock()

        mock_api.get = AsyncMock(
            side_effect=[
                # Workflow with repository
                {"data": {"relationships": {"repository": {"data": {"id": "repo-456"}}}}},
                # Git references
                {
                    "data": [
                        {
                            "id": "resolved-uuid-123",
                            "attributes": {"name": "main", "isDeleted": False},
                        },
                    ]
                },
            ]
        )
        mock_api.post = AsyncMock(return_value={"data": {"id": "build-123", "type": "ciBuildRuns"}})

        await start_build(
            api=mock_api,
            workflow_id="workflow-123",
            source_branch_or_tag="main",
        )

        # Should call GET twice for resolution (workflow + refs)
        assert mock_api.get.call_count == 2

        # Verify resolved UUID was used in POST
        mock_api.post.assert_called_once()
        call_data = mock_api.post.call_args[1]["data"]
        ref_id = call_data["data"]["relationships"]["sourceBranchOrTag"]["data"]["id"]
        assert ref_id == "resolved-uuid-123"

    @pytest.mark.asyncio
    async def test_start_build_without_branch_works(self):
        """Test that builds without branch specification still work."""
        mock_api = AsyncMock()
        mock_api.post = AsyncMock(return_value={"data": {"id": "build-123", "type": "ciBuildRuns"}})

        await start_build(
            api=mock_api,
            workflow_id="workflow-123",
            source_branch_or_tag=None,
        )

        # Should not call GET (no resolution needed)
        mock_api.get.assert_not_called()

        # Should not include sourceBranchOrTag in request
        call_data = mock_api.post.call_args[1]["data"]
        assert "sourceBranchOrTag" not in call_data["data"]["relationships"]


class TestStartBuildByRefId:
    """Test start_build_by_ref_id function (no resolution)."""

    @pytest.mark.asyncio
    async def test_start_build_by_ref_id_uses_id_directly(self):
        """Test that start_build_by_ref_id uses the ID without resolution."""
        mock_api = AsyncMock()
        mock_api.post = AsyncMock(return_value={"data": {"id": "build-123", "type": "ciBuildRuns"}})

        await start_build_by_ref_id(
            api=mock_api,
            workflow_id="workflow-123",
            source_ref_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        )

        # Should NOT call GET - ID used directly
        mock_api.get.assert_not_called()

        # Verify ID was passed through to POST
        mock_api.post.assert_called_once()
        call_data = mock_api.post.call_args[1]["data"]
        ref_id = call_data["data"]["relationships"]["sourceBranchOrTag"]["data"]["id"]
        assert ref_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
