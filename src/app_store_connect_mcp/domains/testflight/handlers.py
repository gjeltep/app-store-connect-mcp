from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import json

from mcp.types import Tool, TextContent
from app_store_connect_mcp.models import (
    BetaFeedbackCrashSubmissionsResponse,
    BetaFeedbackCrashSubmissionResponse,
)

from app_store_connect_mcp.core.protocols import APIClient, DomainHandler
from app_store_connect_mcp.domains.testflight.schemas import get_all_tools
from app_store_connect_mcp.core.errors import AppStoreConnectError, ValidationError
from app_store_connect_mcp.core.constants import APP_STORE_CONNECT_MAX_PAGE_SIZE
from app_store_connect_mcp.utils.parsers import parse_datetime, version_ge, version_le

FIELDS_BFCS: List[str] = [
    "createdDate",
    "comment",
    "email",
    "deviceModel",
    "osVersion",
    "locale",
    "timeZone",
    "architecture",
    "connectionType",
    "pairedAppleWatch",
    "appUptimeInMilliseconds",
    "diskBytesAvailable",
    "diskBytesTotal",
    "batteryPercentage",
    "screenWidthInPoints",
    "screenHeightInPoints",
    "appPlatform",
    "devicePlatform",
    "deviceFamily",
    "buildBundleId",
    "crashLog",
    "build",
    "tester",
]


class TestFlightHandler(DomainHandler):
    """MCP tool definitions and handlers for TestFlight crash management."""

    def __init__(self, api: APIClient):
        self.api = api

    @staticmethod
    def get_tools() -> List[Tool]:
        return get_all_tools()

    @staticmethod
    def get_category() -> str:
        """Get the category name for TestFlight tools."""
        return "TestFlight"

    async def handle_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        try:
            if name == "crashes.list":
                result = await self._get_crash_submissions(
                    app_id=arguments.get("app_id"),
                    filters=arguments.get("filters"),
                    sort=arguments.get("sort", "-createdDate"),
                    limit=arguments.get("limit", 50),
                    include=arguments.get("include"),
                )
            elif name == "crashes.search":
                result = await self._search_crash_submissions(
                    app_id=arguments.get("app_id"),
                    app_platform=arguments.get("app_platform"),
                    device_platform=arguments.get("device_platform", ["IOS"]),
                    os_min_version=arguments.get("os_min_version"),
                    os_max_version=arguments.get("os_max_version"),
                    os_versions=arguments.get("os_versions"),
                    device_model=arguments.get("device_model"),
                    device_model_contains=arguments.get("device_model_contains"),
                    created_since_days=arguments.get("created_since_days"),
                    created_after=arguments.get("created_after"),
                    created_before=arguments.get("created_before"),
                    limit=arguments.get("limit", APP_STORE_CONNECT_MAX_PAGE_SIZE),
                    include=arguments.get("include"),
                    sort=arguments.get("sort", "-createdDate"),
                )
            elif name == "crashes.get_by_id":
                result = await self._get_crash_submission_details(
                    submission_id=arguments["submission_id"],
                    include=arguments.get("include"),
                )
            elif name == "crashes.get_log":
                result = await self._get_crash_log(
                    submission_id=arguments["submission_id"]
                )
            else:
                raise ValidationError(
                    f"Unknown tool: {name}",
                    details={
                        "tool_name": name,
                        "available_tools": [t.name for t in self.get_tools()],
                    },
                )
            return [TextContent(type="text", text=json.dumps(result))]

        except AppStoreConnectError as e:
            # Return structured error information
            error_dict = e.to_dict()
            return [TextContent(type="text", text=json.dumps(error_dict))]
        except Exception as e:
            # Wrap unexpected errors
            error = AppStoreConnectError(
                f"Unexpected error in {name}: {str(e)}",
                details={"tool": name, "arguments": arguments},
            )
            return [TextContent(type="text", text=json.dumps(error.to_dict()))]

    # ----- API calls -----
    async def _get_crash_submissions(
        self,
        app_id: Optional[str] = None,
        filters: Optional[Dict] = None,
        sort: str = "-createdDate",
        limit: int = 50,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        app_id = app_id or self.api.default_app_id
        if not app_id:
            raise ValidationError(
                "app_id is required",
                user_message="Please provide an app_id or set APP_STORE_APP_ID environment variable",
                details={"missing_field": "app_id"},
            )

        endpoint = f"/v1/apps/{app_id}/betaFeedbackCrashSubmissions"

        params = {
            "sort": sort,
            "limit": limit,
        }

        if filters:
            for key, value in filters.items():
                if key == "device_model":
                    params["filter[deviceModel]"] = ",".join(value)
                elif key == "os_version":
                    params["filter[osVersion]"] = ",".join(value)
                elif key == "app_platform":
                    params["filter[appPlatform]"] = ",".join(value)
                elif key == "device_platform":
                    params["filter[devicePlatform]"] = ",".join(value)
                elif key == "build_id":
                    params["filter[build]"] = ",".join(value)
                elif key == "tester_id":
                    params["filter[tester]"] = ",".join(value)

        if include:
            params["include"] = ",".join(include)

        params["fields[betaFeedbackCrashSubmissions]"] = ",".join(FIELDS_BFCS)

        if limit < APP_STORE_CONNECT_MAX_PAGE_SIZE:
            params["limit"] = limit
            raw = await self.api.get(endpoint, params=params)
            try:
                parsed = BetaFeedbackCrashSubmissionsResponse.model_validate(raw)
                return parsed.model_dump(mode="json")
            except Exception:
                return raw

        max_total = limit if limit and limit > 0 else None
        raw = await self.api.get_all_pages(
            endpoint,
            params=params,
            page_size=APP_STORE_CONNECT_MAX_PAGE_SIZE,
            max_total=max_total,
        )
        try:
            parsed = BetaFeedbackCrashSubmissionsResponse.model_validate(raw)
            return parsed.model_dump(mode="json")
        except Exception:
            return raw

    async def _search_crash_submissions(
        self,
        app_id: Optional[str] = None,
        app_platform: Optional[List[str]] = None,
        device_platform: Optional[List[str]] = None,
        os_min_version: Optional[str] = None,
        os_max_version: Optional[str] = None,
        os_versions: Optional[List[str]] = None,
        device_model: Optional[List[str]] = None,
        device_model_contains: Optional[List[str]] = None,
        created_since_days: Optional[int] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: int = APP_STORE_CONNECT_MAX_PAGE_SIZE,
        include: Optional[List[str]] = None,
        sort: str = "-createdDate",
    ) -> Dict[str, Any]:
        app_id = app_id or self.api.default_app_id
        if not app_id:
            raise ValidationError(
                "app_id is required",
                user_message="Please provide an app_id or set APP_STORE_APP_ID environment variable",
                details={"missing_field": "app_id"},
            )

        endpoint = f"/v1/apps/{app_id}/betaFeedbackCrashSubmissions"

        params: Dict[str, Any] = {"sort": sort}
        params["fields[betaFeedbackCrashSubmissions]"] = ",".join(FIELDS_BFCS)

        # Server-side filters to reduce payload where possible
        if app_platform:
            params["filter[appPlatform]"] = ",".join(app_platform)
        if device_model:
            params["filter[deviceModel]"] = ",".join(device_model)
        if os_versions:
            params["filter[osVersion]"] = ",".join(os_versions)

        if include:
            params["include"] = ",".join(include)

        raw = await self.api.get_all_pages(
            endpoint,
            params=params,
            page_size=APP_STORE_CONNECT_MAX_PAGE_SIZE,
            max_total=None,
        )
        data = raw.get("data", [])
        included = raw.get("included", [])

        now_utc = datetime.now(timezone.utc)
        min_dt: Optional[datetime] = None
        max_dt: Optional[datetime] = None
        if created_since_days and created_since_days > 0:
            min_dt = now_utc - timedelta(days=created_since_days)
        arg_min = parse_datetime(created_after)
        arg_max = parse_datetime(created_before)
        if arg_min:
            min_dt = arg_min if not min_dt else max(min_dt, arg_min)
        if arg_max:
            max_dt = arg_max if not max_dt else min(max_dt, arg_max)

        def matches(item: Dict[str, Any]) -> bool:
            attrs = item.get("attributes", {})
            if device_platform:
                if attrs.get("devicePlatform") not in set(device_platform):
                    return False
            os_ver = attrs.get("osVersion") or ""
            if os_min_version and not version_ge(os_ver, os_min_version):
                return False
            if os_max_version and not version_le(os_ver, os_max_version):
                return False
            if device_model_contains:
                model = (attrs.get("deviceModel") or "").lower()
                if not any(substr.lower() in model for substr in device_model_contains):
                    return False
            if min_dt or max_dt:
                created_raw = attrs.get("createdDate")
                created_dt = parse_datetime(created_raw)
                if not created_dt:
                    return False
                if min_dt and created_dt < min_dt:
                    return False
                if max_dt and created_dt > max_dt:
                    return False
            return True

        filtered = [d for d in data if matches(d)]
        if limit > 0:
            filtered = filtered[:limit]

        result: Dict[str, Any] = {"data": filtered}
        if included:
            result["included"] = included
        return result

    async def _get_crash_submission_details(
        self, submission_id: str, include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        endpoint = f"/v1/betaFeedbackCrashSubmissions/{submission_id}"
        params: Dict[str, Any] = {}
        if include:
            params["include"] = ",".join(include)
        params["fields[betaFeedbackCrashSubmissions]"] = ",".join(FIELDS_BFCS)
        raw = await self.api.get(endpoint, params=params)
        try:
            parsed = BetaFeedbackCrashSubmissionResponse.model_validate(raw)
            return parsed.model_dump(mode="json")
        except Exception:
            return raw

    async def _get_crash_log(self, submission_id: str) -> Dict[str, Any]:
        endpoint = f"/v1/betaFeedbackCrashSubmissions/{submission_id}/crashLog"
        params = {"fields[betaCrashLogs]": "logText"}
        return await self.api.get(endpoint, params=params)


__all__ = ["TestFlightHandler"]
