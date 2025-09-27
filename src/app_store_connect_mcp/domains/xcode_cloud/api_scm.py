"""XcodeCloud SCM API operations."""

from typing import Optional, List, Dict, Any

from app_store_connect_mcp.models import (
    ScmProvidersResponse,
    ScmRepositoriesResponse,
    ScmPullRequestsResponse,
    ScmGitReferencesResponse,
)
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.core.protocols import APIClient
from app_store_connect_mcp.domains.xcode_cloud.constants import (
    FIELDS_SCM_PROVIDERS,
    FIELDS_SCM_REPOSITORIES,
    FIELDS_SCM_PULL_REQUESTS,
    FIELDS_SCM_GIT_REFERENCES,
)


async def list_scm_providers(
    api: APIClient,
    limit: int = 50,
) -> Dict[str, Any]:
    """List SCM providers."""
    endpoint = "/v1/scmProviders"

    query = (
        APIQueryBuilder(endpoint)
        .with_limit_and_sort(limit)  # API supports limit but not sort
        .with_fields("scmProviders", FIELDS_SCM_PROVIDERS)
    )

    return await query.execute(api, ScmProvidersResponse)


async def list_repositories(
    api: APIClient,
    scm_provider_id: str,
    limit: int = 50,
    include: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """List repositories for an SCM provider."""
    endpoint = f"/v1/scmProviders/{scm_provider_id}/repositories"

    query = (
        APIQueryBuilder(endpoint)
        .with_limit_and_sort(limit)  # API supports limit but not sort
        .with_fields("scmRepositories", FIELDS_SCM_REPOSITORIES)
        .with_includes(include)
    )

    return await query.execute(api, ScmRepositoriesResponse)


async def list_pull_requests(
    api: APIClient,
    repository_id: str,
    limit: int = 50,
    include: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """List pull requests for a repository."""
    endpoint = f"/v1/scmRepositories/{repository_id}/pullRequests"

    query = (
        APIQueryBuilder(endpoint)
        .with_limit_and_sort(limit)  # API supports limit but not sort
        .with_fields("scmPullRequests", FIELDS_SCM_PULL_REQUESTS)
        .with_includes(include)
    )

    return await query.execute(api, ScmPullRequestsResponse)


async def list_git_references(
    api: APIClient,
    repository_id: str,
    limit: int = 100,
    include: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """List Git references (branches/tags) for a repository."""
    endpoint = f"/v1/scmRepositories/{repository_id}/gitReferences"

    query = (
        APIQueryBuilder(endpoint)
        .with_limit_and_sort(limit)  # API supports limit but not sort
        .with_fields("scmGitReferences", FIELDS_SCM_GIT_REFERENCES)
        .with_includes(include)
    )

    return await query.execute(api, ScmGitReferencesResponse)
