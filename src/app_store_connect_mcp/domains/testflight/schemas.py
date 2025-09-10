from typing import Dict, List

from mcp.types import Tool
from app_store_connect_mcp.core.constants import APP_STORE_CONNECT_MAX_PAGE_SIZE

PLATFORM_ENUM = ["IOS", "MAC_OS", "TV_OS", "VISION_OS"]


def build_crashes_list_tool() -> Tool:
    return Tool(
        name="crashes.list",
        description="[TestFlight] List crash submissions from beta testers",
        inputSchema={
            "type": "object",
            "properties": {
                "app_id": {
                    "type": "string",
                    "description": "The App ID to get crash submissions for; defaults to APP_STORE_APP_ID if unset",
                },
                "filters": {
                    "type": "object",
                    "properties": {
                        "device_model": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by device model",
                        },
                        "os_version": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by OS version",
                        },
                        "app_platform": {
                            "type": "array",
                            "items": {"type": "string", "enum": PLATFORM_ENUM},
                            "description": "Filter by app platform",
                        },
                        "device_platform": {
                            "type": "array",
                            "items": {"type": "string", "enum": PLATFORM_ENUM},
                            "description": "Filter by device platform",
                        },
                        "build_id": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by build ID(s)",
                        },
                        "tester_id": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by tester ID(s)",
                        },
                    },
                },
                "sort": {
                    "type": "string",
                    "enum": ["createdDate", "-createdDate"],
                    "description": "Sort order for results",
                    "default": "-createdDate",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 50,
                    "minimum": 1,
                    "maximum": APP_STORE_CONNECT_MAX_PAGE_SIZE,
                },
                "include": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["build", "tester", "crashLog"],
                    },
                    "description": "Related resources to include in the response. (Enum may be expanded from the OpenAPI spec at runtime)",
                },
            },
        },
    )


def build_crashes_search_tool() -> Tool:
    return Tool(
        name="crashes.search",
        description=(
            "[TestFlight] Search crash submissions with advanced filtering. "
            "Supports device platform, OS version range, device model matching, and date windows."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "app_id": {
                    "type": "string",
                    "description": "App ID; defaults to APP_STORE_APP_ID if unset",
                },
                "app_platform": {
                    "type": "array",
                    "items": {"type": "string", "enum": PLATFORM_ENUM},
                    "description": "Filter by app platform (server-side)",
                },
                "device_platform": {
                    "type": "array",
                    "items": {"type": "string", "enum": PLATFORM_ENUM},
                    "description": "Filter by device platform (post-filtered)",
                    "default": ["IOS"],
                },
                "os_min_version": {
                    "type": "string",
                    "description": "Inclusive minimum OS version (e.g., '16.0')",
                },
                "os_max_version": {
                    "type": "string",
                    "description": "Inclusive maximum OS version (e.g., '17.9')",
                },
                "os_versions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exact OS versions to filter server-side (use with or instead of min/max)",
                },
                "device_model": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exact device models to filter server-side",
                },
                "device_model_contains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Match device model substrings (case-insensitive)",
                },
                "created_since_days": {
                    "type": "integer",
                    "description": "Include only submissions created within the past N days (inclusive)",
                    "minimum": 1,
                },
                "created_after": {
                    "type": "string",
                    "description": "ISO-8601 datetime (UTC recommended). Include submissions with createdDate >= this",
                },
                "created_before": {
                    "type": "string",
                    "description": "ISO-8601 datetime (UTC recommended). Include submissions with createdDate <= this",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of filtered results to return",
                    "default": APP_STORE_CONNECT_MAX_PAGE_SIZE,
                    "minimum": 1,
                },
                "include": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["build", "tester", "crashLog"],
                    },
                    "description": "Related resources to include in the response. (Enum may be expanded from the OpenAPI spec at runtime)",
                },
                "sort": {
                    "type": "string",
                    "enum": ["createdDate", "-createdDate"],
                    "description": "Sort order before filtering",
                    "default": "-createdDate",
                },
            },
        },
    )


def build_crashes_get_by_id_tool() -> Tool:
    return Tool(
        name="crashes.get_by_id",
        description="[TestFlight] Get detailed information about a specific crash submission",
        inputSchema={
            "type": "object",
            "properties": {
                "submission_id": {
                    "type": "string",
                    "description": "The ID of the crash submission",
                },
                "include": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["build", "tester", "crashLog"],
                    },
                    "description": "Related resources to include in the response",
                },
            },
            "required": ["submission_id"],
        },
    )


def build_crashes_get_log_tool() -> Tool:
    return Tool(
        name="crashes.get_log",
        description="[TestFlight] Get the raw crash log text for a specific crash submission",
        inputSchema={
            "type": "object",
            "properties": {
                "submission_id": {
                    "type": "string",
                    "description": "The ID of the crash submission",
                }
            },
            "required": ["submission_id"],
        },
    )


def get_all_tools() -> List[Tool]:
    return [
        build_crashes_list_tool(),
        build_crashes_search_tool(),
        build_crashes_get_by_id_tool(),
        build_crashes_get_log_tool(),
    ]


__all__ = [
    "build_crashes_list_tool",
    "build_crashes_search_tool",
    "build_crashes_get_by_id_tool",
    "build_crashes_get_log_tool",
    "get_all_tools",
]
