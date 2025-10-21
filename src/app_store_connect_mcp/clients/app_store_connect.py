import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app_store_connect_mcp.clients.http_client import BaseHTTPClient
from app_store_connect_mcp.core.constants import (
    JWT_AUDIENCE,
    JWT_EARLY_RENEWAL_SECONDS,
    JWT_TTL_SECONDS,
)
from app_store_connect_mcp.core.errors import AuthenticationError, ConfigurationError
from app_store_connect_mcp.core.protocols import APIClient


class AppStoreConnectAPI(BaseHTTPClient, APIClient):
    """Async App Store Connect API client."""

    def __init__(self, config: dict[str, str | None] | None = None):
        # Load from config dict if provided, otherwise from environment
        if config:
            self.key_id = config.get("APP_STORE_KEY_ID")
            self.issuer_id = config.get("APP_STORE_ISSUER_ID")
            self.private_key_path = config.get("APP_STORE_PRIVATE_KEY_PATH")
            self._default_app_id = config.get("APP_STORE_APP_ID")
            self.key_type = (config.get("APP_STORE_KEY_TYPE") or "team").lower()
            self.scope = config.get("APP_STORE_SCOPE")
            self.subject = config.get("APP_STORE_SUBJECT")
        else:
            # Read directly from environment (production mode)
            self.key_id = os.getenv("APP_STORE_KEY_ID")
            self.issuer_id = os.getenv("APP_STORE_ISSUER_ID")
            self.private_key_path = os.getenv("APP_STORE_PRIVATE_KEY_PATH")
            self._default_app_id = os.getenv("APP_STORE_APP_ID")
            self.key_type = os.getenv("APP_STORE_KEY_TYPE", "team").lower()
            self.scope = os.getenv("APP_STORE_SCOPE")
            self.subject = os.getenv("APP_STORE_SUBJECT")

        # JWT Configuration
        self._private_key_cache: str | None = None
        self._cached_token: str | None = None
        self._cached_token_expiry: datetime | None = None

        # Validate required configuration
        if not all([self.key_id, self.issuer_id, self.private_key_path]):
            missing = []
            if not self.key_id:
                missing.append("APP_STORE_KEY_ID")
            if not self.issuer_id:
                missing.append("APP_STORE_ISSUER_ID")
            if not self.private_key_path:
                missing.append("APP_STORE_PRIVATE_KEY_PATH")
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}",
                details={"missing_variables": missing},
            )

        # Initialize base HTTP client
        super().__init__(
            base_url="https://api.appstoreconnect.apple.com",
            headers={
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def _load_private_key(self) -> str:
        """Read and cache the private key contents from the provided path."""
        if self._private_key_cache:
            return self._private_key_cache
        if not self.private_key_path:
            raise ConfigurationError("APP_STORE_PRIVATE_KEY_PATH is not set")
        try:
            with open(self.private_key_path, encoding="utf-8") as f:
                self._private_key_cache = f.read()
            return self._private_key_cache
        except FileNotFoundError as e:
            raise ConfigurationError(
                f"Private key file not found at path: {self.private_key_path}",
                details={"path": self.private_key_path},
            ) from e
        except Exception as e:
            raise ConfigurationError(
                "Failed to read private key file",
                details={"path": self.private_key_path, "error": str(e)},
            ) from e

    def _generate_jwt(self) -> str:
        """Generate a signed JWT for App Store Connect API using ES256.

        Caches the token until shortly before expiration to avoid re-signing on every request.
        """
        # Return cached token if still valid
        now = datetime.now(UTC)
        if (
            self._cached_token
            and self._cached_token_expiry
            and now < self._cached_token_expiry - timedelta(seconds=JWT_EARLY_RENEWAL_SECONDS)
        ):
            return self._cached_token

        if not all([self.key_id, self.issuer_id, self.private_key_path]):
            missing = []
            if not self.key_id:
                missing.append("APP_STORE_KEY_ID")
            if not self.issuer_id:
                missing.append("APP_STORE_ISSUER_ID")
            if not self.private_key_path:
                missing.append("APP_STORE_PRIVATE_KEY_PATH")
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}",
                details={"missing_variables": missing},
            )

        private_key = self._load_private_key()

        issued_at = int(time.time())
        expires_at = issued_at + JWT_TTL_SECONDS

        # Build payload based on key type (team vs individual)
        if self.key_type == "team":
            payload = {
                "iss": self.issuer_id,
                "iat": issued_at,
                "exp": expires_at,
                "aud": JWT_AUDIENCE,
            }
        elif self.key_type == "individual":
            payload = {
                "sub": self.subject or "user",
                "iat": issued_at,
                "exp": expires_at,
                "aud": JWT_AUDIENCE,
            }
        else:
            raise ConfigurationError(
                "APP_STORE_KEY_TYPE must be 'team' or 'individual'",
                details={"APP_STORE_KEY_TYPE": self.key_type},
            )

        # Optional scope claim (comma-separated env var -> list)
        if self.scope:
            scope_values = [s.strip() for s in self.scope.split(",") if s.strip()]
            if scope_values:
                payload["scope"] = scope_values

        headers = {
            "alg": "ES256",
            "kid": self.key_id,
            "typ": "JWT",
        }

        try:
            token: str = jwt.encode(
                payload,
                private_key,
                algorithm="ES256",
                headers=headers,
            )
        except Exception as e:
            raise AuthenticationError(
                "Failed to generate JWT for App Store Connect API",
                details={"error": str(e)},
            )

        # Cache token and expiry
        self._cached_token = token
        self._cached_token_expiry = datetime.fromtimestamp(expires_at, tz=UTC)
        return token

    @property
    def default_app_id(self) -> str | None:
        """Default app ID for operations."""
        return self._default_app_id

    def ensure_app_id(self, app_id: str | None) -> str:
        """Ensure we have a valid app_id, using the default if needed.

        Args:
            app_id: The provided app_id or None

        Returns:
            The app_id to use

        Raises:
            ValidationError: If no app_id is provided and no default is set
        """
        from app_store_connect_mcp.core.errors import ValidationError

        app_id = app_id or self._default_app_id
        if not app_id:
            raise ValidationError(
                "app_id is required",
                user_message="Please provide an app_id or set APP_STORE_APP_ID environment variable",
                details={"missing_field": "app_id"},
            )
        return app_id

    async def patch(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute PATCH request."""
        return await self._execute_request("PATCH", endpoint, json=data, params=params)

    async def get_url(self, url: str) -> dict[str, Any]:
        """Get a specific URL (for pagination links)."""
        return await self._execute_request("GET", url)

    async def _execute_request(
        self,
        method: str,
        url_or_endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Attach Authorization header with fresh JWT and delegate to base client."""
        # Ensure Authorization header is present and fresh
        request_headers: dict[str, str] = {}
        if "headers" in kwargs and kwargs["headers"]:
            # Make a shallow copy to avoid mutating caller's dict
            request_headers = dict(kwargs.pop("headers"))
        request_headers["Authorization"] = f"Bearer {self._generate_jwt()}"

        return await super()._execute_request(
            method,
            url_or_endpoint,
            headers=request_headers,
            **kwargs,
        )
