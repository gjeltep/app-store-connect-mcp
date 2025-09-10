"""Constants used throughout the App Store Connect MCP server."""

# API Pagination
APP_STORE_CONNECT_MAX_PAGE_SIZE = 200
"""Maximum number of items per page in App Store Connect API responses."""

# JWT Authentication
JWT_TTL_SECONDS = 1200  # 20 minutes
"""JWT token time-to-live in seconds (max per Apple docs)."""

JWT_EARLY_RENEWAL_SECONDS = 60
"""Renew JWT token this many seconds before expiry."""

JWT_AUDIENCE = "appstoreconnect-v1"
"""JWT audience claim for App Store Connect API."""
