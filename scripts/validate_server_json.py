#!/usr/bin/env python3
"""Validate server.json against the official MCP registry schema."""

import json
import sys
from pathlib import Path

try:
    import httpx
    import jsonschema
except ImportError:
    print("Error: Required packages not installed.", file=sys.stderr)
    print("Install with: uv pip install jsonschema httpx", file=sys.stderr)
    sys.exit(1)

# Schema URL from MCP registry
SCHEMA_URL = "https://static.modelcontextprotocol.io/schemas/2025-09-16/server.schema.json"

# Path to server.json (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
SERVER_JSON_PATH = PROJECT_ROOT / "server.json"


def fetch_schema() -> dict:
    """Fetch the JSON schema from the official MCP registry."""
    try:
        response = httpx.get(SCHEMA_URL, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"Error fetching schema from {SCHEMA_URL}: {e}", file=sys.stderr)
        sys.exit(1)


def load_server_json() -> dict:
    """Load the server.json file."""
    if not SERVER_JSON_PATH.exists():
        print(f"Error: server.json not found at {SERVER_JSON_PATH}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(SERVER_JSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in server.json: {e}", file=sys.stderr)
        sys.exit(1)


def validate_server_json(server_config: dict, schema: dict) -> None:
    """Validate server.json against the schema."""
    try:
        jsonschema.validate(instance=server_config, schema=schema)
        print("✅ server.json is valid!")
    except jsonschema.ValidationError as e:
        print("❌ Validation failed:", file=sys.stderr)
        print(f"  Path: {' -> '.join(str(p) for p in e.path)}", file=sys.stderr)
        print(f"  Error: {e.message}", file=sys.stderr)
        if e.context:
            print("  Additional errors:", file=sys.stderr)
            for ctx_error in e.context:
                print(f"    - {ctx_error.message}", file=sys.stderr)
        sys.exit(1)
    except jsonschema.SchemaError as e:
        print(f"Error: Invalid schema: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main validation function."""
    print("Fetching MCP registry schema...")
    schema = fetch_schema()

    print(f"Loading {SERVER_JSON_PATH}...")
    server_config = load_server_json()

    print("Validating server.json...")
    validate_server_json(server_config, schema)


if __name__ == "__main__":
    main()