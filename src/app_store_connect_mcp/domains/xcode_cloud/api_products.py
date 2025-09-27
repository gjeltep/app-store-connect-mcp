"""API methods for Xcode Cloud products and workflows."""

from typing import Optional, List, Dict, Any

from app_store_connect_mcp.models import (
    CiProductsResponse,
    CiProductResponse,
    CiWorkflowsResponse,
    CiWorkflowResponse,
)
from app_store_connect_mcp.core.query_builder import APIQueryBuilder
from app_store_connect_mcp.core.protocols import APIClient


# Field definitions for products and workflows
FIELDS_CI_PRODUCTS: List[str] = [
    "name",
    "createdDate",
    "productType",
]

FIELDS_CI_WORKFLOWS: List[str] = [
    "name",
    "description",
    "isEnabled",
    "isLockedForEditing",
    "containerFilePath",
    "lastModifiedDate",
]

# Filter mappings for server-side filtering
PRODUCT_FILTER_MAPPING = {
    "product_type": "productType",
}

WORKFLOW_FILTER_MAPPING = {
    "is_enabled": "isEnabled",
}


async def list_products(
    api: APIClient,
    filters: Optional[Dict] = None,
    limit: int = 50,
    include: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """List all Xcode Cloud products."""
    endpoint = "/v1/ciProducts"

    query = (
        APIQueryBuilder(endpoint)
        .with_limit_and_sort(limit)  # No sort parameter supported by API
        .with_filters(filters, PRODUCT_FILTER_MAPPING)
        .with_fields("ciProducts", FIELDS_CI_PRODUCTS)
        .with_includes(include)
    )

    return await query.execute(api, CiProductsResponse)


async def get_product(
    api: APIClient,
    product_id: str,
    include: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Get detailed information about a specific Xcode Cloud product."""
    endpoint = f"/v1/ciProducts/{product_id}"

    query = (
        APIQueryBuilder(endpoint)
        .with_fields("ciProducts", FIELDS_CI_PRODUCTS)
        .with_includes(include)
    )

    return await query.execute(api, CiProductResponse)


async def list_workflows(
    api: APIClient,
    product_id: str,
    filters: Optional[Dict] = None,
    limit: int = 50,
    include: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """List workflows for a product."""
    endpoint = f"/v1/ciProducts/{product_id}/workflows"

    query = (
        APIQueryBuilder(endpoint)
        .with_limit_and_sort(limit)  # No sort parameter supported by API
        .with_filters(filters, WORKFLOW_FILTER_MAPPING)
        .with_fields("ciWorkflows", FIELDS_CI_WORKFLOWS)
        .with_includes(include)
    )

    return await query.execute(api, CiWorkflowsResponse)


async def get_workflow(
    api: APIClient,
    workflow_id: str,
    include: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Get detailed information about a specific workflow."""
    endpoint = f"/v1/ciWorkflows/{workflow_id}"

    query = (
        APIQueryBuilder(endpoint)
        .with_fields("ciWorkflows", FIELDS_CI_WORKFLOWS)
        .with_includes(include)
    )

    return await query.execute(api, CiWorkflowResponse)
