"""Structured error handling for App Store Connect MCP server."""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCategory(Enum):
    """Categories of errors for better user guidance."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    NETWORK = "network"
    CONFIGURATION = "configuration"


class AppStoreConnectError(Exception):
    """Base exception for all App Store Connect MCP errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.API_ERROR,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ):
        self.message = message
        self.category = category
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or self._get_default_user_message()
        super().__init__(self.message)

    def _get_default_user_message(self) -> str:
        """Generate user-friendly message based on category."""
        category_messages = {
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your API credentials.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to access this resource.",
            ErrorCategory.VALIDATION: "The request contains invalid parameters.",
            ErrorCategory.NOT_FOUND: "The requested resource was not found.",
            ErrorCategory.RATE_LIMIT: "API rate limit exceeded. Please try again later.",
            ErrorCategory.API_ERROR: "An error occurred with the App Store Connect API.",
            ErrorCategory.NETWORK: "Network connection error. Please check your connection.",
            ErrorCategory.CONFIGURATION: "Configuration error. Please check your environment variables.",
        }
        return category_messages.get(self.category, self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to structured dictionary for MCP responses."""
        return {
            "error": {
                "message": self.message,
                "category": self.category.value,
                "status_code": self.status_code,
                "details": self.details,
                "user_message": self.user_message,
            }
        }


class AuthenticationError(AppStoreConnectError):
    """Raised when API authentication fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.AUTHENTICATION, **kwargs)


class AuthorizationError(AppStoreConnectError):
    """Raised when user lacks permissions for a resource."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.AUTHORIZATION, **kwargs)


class ValidationError(AppStoreConnectError):
    """Raised when request validation fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)


class ResourceNotFoundError(AppStoreConnectError):
    """Raised when a requested resource doesn't exist."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.NOT_FOUND, **kwargs)


class RateLimitError(AppStoreConnectError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.RATE_LIMIT, **kwargs)


class NetworkError(AppStoreConnectError):
    """Raised when network operations fail."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)


class ConfigurationError(AppStoreConnectError):
    """Raised when configuration is missing or invalid."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.CONFIGURATION, **kwargs)


def handle_http_error(
    status_code: int, response_body: Optional[Dict[str, Any]] = None
) -> AppStoreConnectError:
    """Map HTTP status codes to appropriate exceptions."""
    error_message = (
        response_body.get("errors", [{}])[0].get("detail", "") if response_body else ""
    )

    if status_code == 401:
        return AuthenticationError(
            f"Authentication failed: {error_message or 'Invalid or expired API credentials'}",
            status_code=status_code,
            details=response_body,
        )
    elif status_code == 403:
        return AuthorizationError(
            f"Access denied: {error_message or 'Insufficient permissions'}",
            status_code=status_code,
            details=response_body,
        )
    elif status_code == 404:
        return ResourceNotFoundError(
            f"Resource not found: {error_message or 'The requested resource does not exist'}",
            status_code=status_code,
            details=response_body,
        )
    elif status_code == 422:
        return ValidationError(
            f"Validation error: {error_message or 'Invalid request parameters'}",
            status_code=status_code,
            details=response_body,
        )
    elif status_code == 429:
        return RateLimitError(
            f"Rate limit exceeded: {error_message or 'Too many requests'}",
            status_code=status_code,
            details=response_body,
        )
    elif status_code >= 500:
        return AppStoreConnectError(
            f"Server error: {error_message or 'App Store Connect API error'}",
            category=ErrorCategory.API_ERROR,
            status_code=status_code,
            details=response_body,
        )
    else:
        return AppStoreConnectError(
            f"HTTP {status_code}: {error_message or 'Unexpected error'}",
            status_code=status_code,
            details=response_body,
        )
