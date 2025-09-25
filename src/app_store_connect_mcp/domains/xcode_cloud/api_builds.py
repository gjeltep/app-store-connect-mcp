"""API methods for Xcode Cloud builds, artifacts, issues, and test results."""

from typing import Optional, List, Dict, Any, Callable

from app_store_connect_mcp.models import (
    CiBuildRunsResponse,
    CiBuildRunResponse,
    CiBuildRunCreateRequest,
)
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.core.protocols import APIClient
from app_store_connect_mcp.core.errors import ValidationError


# Field definitions for builds and related resources
FIELDS_CI_BUILD_RUNS: List[str] = [
    "number",
    "createdDate",
    "startedDate",
    "finishedDate",
    "sourceCommit",
    "destinationCommit",
    "isPullRequestBuild",
    "issueCounts",
    "executionProgress",
    "completionStatus",
    "startReason",
    "cancelReason",
]

FIELDS_CI_ARTIFACTS: List[str] = [
    "fileType",
    "fileName",
    "fileSize",
    "downloadUrl",
]

FIELDS_CI_ISSUES: List[str] = [
    "issueType",
    "message",
    "fileSource",
    "category",
]

FIELDS_CI_TEST_RESULTS: List[str] = [
    "className",
    "name",
    "status",
    "message",
    "fileSource",
    "destinationTestResults",
]

# Filter mappings for server-side filtering
BUILD_FILTER_MAPPING = {
    "execution_progress": "executionProgress",
    "completion_status": "completionStatus",
    "is_pull_request_build": "isPullRequestBuild",
}


async def list_builds(
    api: APIClient,
    product_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    filters: Optional[Dict] = None,
    sort: str = "-number",
    limit: int = 50,
    include: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """List builds for a product or workflow."""
    # Determine the appropriate endpoint
    if workflow_id:
        endpoint = f"/v1/ciWorkflows/{workflow_id}/buildRuns"
    elif product_id:
        endpoint = f"/v1/ciProducts/{product_id}/buildRuns"
    else:
        raise ValidationError(
            "Missing required parameter: either product_id or workflow_id must be provided",
            details={"product_id": product_id, "workflow_id": workflow_id}
        )

    # Build query with common parameters
    query = (
        APIQueryBuilder(endpoint)
        .with_pagination(limit, sort)
        .with_filters(filters, BUILD_FILTER_MAPPING)
        .with_fields("ciBuildRuns", FIELDS_CI_BUILD_RUNS)
        .with_includes(include)
    )

    return await query.execute(api, CiBuildRunsResponse)


async def get_build(
    api: APIClient,
    build_id: str,
    include: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Get detailed information about a specific build."""
    endpoint = f"/v1/ciBuildRuns/{build_id}"

    query = (
        APIQueryBuilder(endpoint)
        .with_fields("ciBuildRuns", FIELDS_CI_BUILD_RUNS)
        .with_includes(include)
    )

    return await query.execute(api, CiBuildRunResponse)


async def _fetch_action_resources(
    api: APIClient,
    build_id: str,
    resource_endpoint_suffix: str,
    resource_fields_name: str,
    resource_fields: List[str],
    action_fields: List[str],
    limit: int,
    filter_actions: Optional[Callable[[Dict], bool]] = None,
) -> Dict[str, Any]:
    """Helper to fetch resources from build actions.

    This DRY helper handles the common pattern of:
    1. Fetching all actions for a build
    2. Iterating through actions to get their resources
    3. Augmenting resources with action context

    Args:
        api: API client
        build_id: Build run ID
        resource_endpoint_suffix: Endpoint suffix after /v1/ciBuildActions/{action_id}/
        resource_fields_name: Field name for the resource (e.g., "ciArtifacts")
        resource_fields: Fields to request for the resource
        action_fields: Fields to request for actions
        limit: Max resources per action
        filter_actions: Optional filter to only process certain actions
    """
    # First, get the build actions for this build run
    actions_endpoint = f"/v1/ciBuildRuns/{build_id}/actions"
    actions_query = (
        APIQueryBuilder(actions_endpoint)
        .with_pagination(200)  # Get all actions
        .with_fields("ciBuildActions", action_fields)
    )

    actions_response = await actions_query.execute(api)

    # Collect all resources from all actions
    all_resources = []
    actions_data = actions_response.get("data", [])

    for action in actions_data:
        action_id = action.get("id")

        # Apply filter if provided
        if filter_actions and not filter_actions(action):
            continue

        if action_id:
            # Get resources for this specific action
            resource_endpoint = f"/v1/ciBuildActions/{action_id}/{resource_endpoint_suffix}"
            resource_query = (
                APIQueryBuilder(resource_endpoint)
                .with_pagination(limit)
                .with_fields(resource_fields_name, resource_fields)
            )

            resource_response = await resource_query.execute(api)
            resources = resource_response.get("data", [])

            # Add action context to each resource
            for resource in resources:
                resource["_action"] = {
                    "id": action_id,
                    "name": action.get("attributes", {}).get("name"),
                    "actionType": action.get("attributes", {}).get("actionType"),
                }
                all_resources.append(resource)

    # Return combined response
    return {
        "data": all_resources,
        "meta": {"total": len(all_resources)},
    }


async def start_build(
    api: APIClient,
    workflow_id: str,
    source_branch_or_tag: Optional[str] = None,
    pull_request_number: Optional[int] = None,
) -> Dict[str, Any]:
    """Start a new build for a workflow."""
    endpoint = "/v1/ciBuildRuns"

    # Prepare the request data
    request_data = {
        "data": {
            "type": "ciBuildRuns",
            "relationships": {
                "workflow": {"data": {"type": "ciWorkflows", "id": workflow_id}}
            },
        }
    }

    # Add source branch/tag or pull request if specified
    if source_branch_or_tag:
        request_data["data"]["relationships"]["sourceBranchOrTag"] = {
            "data": {"type": "scmGitReferences", "id": source_branch_or_tag}
        }

    if pull_request_number:
        request_data["data"]["relationships"]["pullRequest"] = {
            "data": {"type": "scmPullRequests", "id": str(pull_request_number)}
        }

    # Make the POST request
    response = await api.post(endpoint, data=request_data)

    # Parse with the model if available
    try:
        parsed = CiBuildRunResponse.model_validate(response)
        return parsed.model_dump(mode="json")
    except Exception:
        return response


async def list_artifacts(
    api: APIClient,
    build_id: str,
    limit: int = 50,
) -> Dict[str, Any]:
    """List artifacts for a build."""
    return await _fetch_action_resources(
        api=api,
        build_id=build_id,
        resource_endpoint_suffix="artifacts",
        resource_fields_name="ciArtifacts",
        resource_fields=FIELDS_CI_ARTIFACTS,
        action_fields=["name", "actionType"],
        limit=limit,
    )


async def list_issues(
    api: APIClient,
    build_id: str,
    limit: int = 100,
) -> Dict[str, Any]:
    """List issues for a build."""
    return await _fetch_action_resources(
        api=api,
        build_id=build_id,
        resource_endpoint_suffix="issues",
        resource_fields_name="ciIssues",
        resource_fields=FIELDS_CI_ISSUES,
        action_fields=["name", "actionType", "issueCounts"],
        limit=limit,
    )


async def list_test_results(
    api: APIClient,
    build_id: str,
    limit: int = 100,
) -> Dict[str, Any]:
    """List test results for a build."""
    # Filter to only process TEST actions
    def is_test_action(action: Dict) -> bool:
        action_type = action.get("attributes", {}).get("actionType")
        return action_type and "TEST" in str(action_type).upper()

    return await _fetch_action_resources(
        api=api,
        build_id=build_id,
        resource_endpoint_suffix="testResults",
        resource_fields_name="ciTestResults",
        resource_fields=FIELDS_CI_TEST_RESULTS,
        action_fields=["name", "actionType"],
        limit=limit,
        filter_actions=is_test_action,
    )