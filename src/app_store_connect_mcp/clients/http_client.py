"""Base HTTP client with structured error handling."""

from typing import Any

import httpx

from app_store_connect_mcp.core.errors import (
    AppStoreConnectError,
    NetworkError,
    handle_http_error,
)


class BaseHTTPClient:
    """Base class for HTTP clients with consistent error handling."""

    def __init__(
        self,
        base_url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers or {},
            timeout=timeout,
        )

    async def aclose(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _handle_response(self, response: httpx.Response) -> dict[str, Any] | None:
        """Process response and handle errors consistently."""
        if response.status_code >= 400:
            try:
                error_body = response.json()
            except Exception:
                error_body = None
            raise handle_http_error(response.status_code, error_body)

        # Handle empty responses (e.g., 204 No Content)
        if response.status_code == 204 or not response.content:
            return None

        return response.json()

    async def _execute_request(
        self, method: str, url_or_endpoint: str, **kwargs
    ) -> dict[str, Any] | None:
        """Execute HTTP request with structured error handling."""
        context = {
            "method": method,
            "url": url_or_endpoint,
            **{
                k: v for k, v in kwargs.items() if k not in ["headers", "auth"]
            },  # Exclude sensitive data
        }

        try:
            response = await self._client.request(method, url_or_endpoint, **kwargs)
            return await self._handle_response(response)
        except httpx.NetworkError as e:
            raise NetworkError(
                f"Network error during {method} {url_or_endpoint}: {str(e)}",
                details=context,
            )
        except httpx.TimeoutException as e:
            raise NetworkError(
                f"Request timeout during {method} {url_or_endpoint}: {str(e)}",
                details=context,
            )
        except AppStoreConnectError:
            # Re-raise our custom errors as-is
            raise
        except Exception as e:
            raise AppStoreConnectError(
                f"Unexpected error during {method} {url_or_endpoint}: {str(e)}",
                details=context,
            )

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute GET request."""
        return await self._execute_request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute POST request."""
        return await self._execute_request("POST", endpoint, json=data)

    async def put(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute PUT request."""
        return await self._execute_request("PUT", endpoint, json=data)

    async def patch(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute PATCH request."""
        return await self._execute_request("PATCH", endpoint, json=data)

    async def delete(self, endpoint: str) -> None:
        """Execute DELETE request."""
        await self._execute_request("DELETE", endpoint)
