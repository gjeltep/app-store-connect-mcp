"""Xcode Cloud domain handler for MCP tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app_store_connect_mcp.core.base_handler import BaseHandler

# Import API methods from sub-modules
from . import api_builds, api_products, api_scm

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


class XcodeCloudHandler(BaseHandler):
    """MCP tool definitions and handlers for Xcode Cloud management."""

    @staticmethod
    def get_category() -> str:
        """Get the category name for Xcode Cloud tools."""
        return "XcodeCloud"

    def register_tools(self, mcp: FastMCP) -> None:
        """Register all Xcode Cloud domain tools with the FastMCP server."""

        # Product management tools
        @mcp.tool()
        async def products_list(
            filters: dict | None = None,
            limit: int = 50,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[XcodeCloud/Products] List all Xcode Cloud products."""
            return await api_products.list_products(
                api=self.api, filters=filters, limit=limit, include=include
            )

        @mcp.tool()
        async def products_get(
            product_id: str,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[XcodeCloud/Products] Get detailed information about a specific Xcode Cloud product."""
            return await api_products.get_product(
                api=self.api, product_id=product_id, include=include
            )

        # Workflow management tools
        @mcp.tool()
        async def workflows_list(
            product_id: str,
            filters: dict | None = None,
            limit: int = 50,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[XcodeCloud/Workflows] List workflows for an Xcode Cloud product. Note: Create/update/delete operations are not supported for safety."""
            return await api_products.list_workflows(
                api=self.api,
                product_id=product_id,
                filters=filters,
                limit=limit,
                include=include,
            )

        @mcp.tool()
        async def workflows_get(
            workflow_id: str,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[XcodeCloud/Workflows] Get detailed information about a specific workflow. Note: Create/update/delete operations are not supported for safety."""
            return await api_products.get_workflow(
                api=self.api, workflow_id=workflow_id, include=include
            )

        # Build management tools
        @mcp.tool()
        async def builds_list(
            product_id: str | None = None,
            workflow_id: str | None = None,
            filters: dict | None = None,
            sort: str = "-number",
            limit: int = 50,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[XcodeCloud/Builds] List builds for a product or workflow. Requires either product_id or workflow_id."""
            return await api_builds.list_builds(
                api=self.api,
                product_id=product_id,
                workflow_id=workflow_id,
                filters=filters,
                sort=sort,
                limit=limit,
                include=include,
            )

        @mcp.tool()
        async def builds_get(
            build_id: str,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[XcodeCloud/Builds] Get detailed information about a specific build."""
            return await api_builds.get_build(api=self.api, build_id=build_id, include=include)

        @mcp.tool()
        async def builds_start(
            workflow_id: str,
            source_branch_or_tag: str | None = None,
            pull_request_number: int | None = None,
        ) -> dict[str, Any]:
            """[XcodeCloud/Builds] Start a new build for a workflow."""
            return await api_builds.start_build(
                api=self.api,
                workflow_id=workflow_id,
                source_branch_or_tag=source_branch_or_tag,
                pull_request_number=pull_request_number,
            )

        # Build artifacts and results tools
        @mcp.tool()
        async def artifacts_list(
            build_id: str,
            limit: int = 50,
        ) -> dict[str, Any]:
            """[XcodeCloud/BuildArtifacts] List artifacts for a build."""
            return await api_builds.list_artifacts(api=self.api, build_id=build_id, limit=limit)

        @mcp.tool()
        async def issues_list(
            build_id: str,
            limit: int = 100,
        ) -> dict[str, Any]:
            """[XcodeCloud/BuildArtifacts] List issues for a build."""
            return await api_builds.list_issues(api=self.api, build_id=build_id, limit=limit)

        @mcp.tool()
        async def test_results_list(
            build_id: str,
            limit: int = 100,
        ) -> dict[str, Any]:
            """[XcodeCloud/BuildArtifacts] List test results for a build."""
            return await api_builds.list_test_results(api=self.api, build_id=build_id, limit=limit)

        # SCM management tools
        @mcp.tool()
        async def scm_providers_list(
            limit: int = 50,
        ) -> dict[str, Any]:
            """[XcodeCloud/SCM] List SCM providers configured for Xcode Cloud."""
            return await api_scm.list_scm_providers(api=self.api, limit=limit)

        @mcp.tool()
        async def repositories_list(
            scm_provider_id: str,
            limit: int = 50,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[XcodeCloud/SCM] List Git repositories for an SCM provider."""
            return await api_scm.list_repositories(
                api=self.api,
                scm_provider_id=scm_provider_id,
                limit=limit,
                include=include,
            )

        @mcp.tool()
        async def pull_requests_list(
            repository_id: str,
            limit: int = 50,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[XcodeCloud/SCM] List pull requests for a repository."""
            return await api_scm.list_pull_requests(
                api=self.api,
                repository_id=repository_id,
                limit=limit,
                include=include,
            )

        @mcp.tool()
        async def git_references_list(
            repository_id: str,
            limit: int = 100,
            include: list[str] | None = None,
        ) -> dict[str, Any]:
            """[XcodeCloud/SCM] List Git references (branches/tags) for a repository."""
            return await api_scm.list_git_references(
                api=self.api,
                repository_id=repository_id,
                limit=limit,
                include=include,
            )
