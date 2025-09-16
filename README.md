## App Store Connect MCP Server

Talk to App Store Connect about your app. Modular tools, async I/O, and OpenAPI‑driven typing so your agent stays accurate as Apple evolves.

### Why this is different
- **Spec‑aware**: Fields and enums are derived from Apple’s OpenAPI spec at runtime, reducing drift and surprise breakage.
- **Fast by default**: Async `httpx` client, server‑side filtering, and smart pagination to keep payloads lean.
- **Smart filtering**: Server‑side + client‑side filtering with chainable filter engine for complex queries.
- **Modular domains**: Clean separation of tool schemas and handlers; add new domains without touching the core.
- **MCP‑native**: Stdio transport, capability declarations, and tool wiring align with the official SDK [python‑sdk README](https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file).

### Quickstart
1) Install

```bash
uv pip install -e .
```

2) Configure

```bash
cp .env.example .env
# Fill in env variables per comments
```

3) Run (stdio)

```bash
app-store-connect-mcp
```

Use with any MCP‑compatible client; the server announces tools and handles calls over stdio.

### Generate/update API models
- Models are generated from Apple’s official OpenAPI spec (fetched on demand).
- Default source fetched from  [Apple](https://developer.apple.com/sample-code/app-store-connect/app-store-connect-openapi-specification.zip).
- Override with `APP_STORE_CONNECT_OPENAPI_URL` to point to a local JSON spec.

Generate:

```bash
uv pip install -e .[dev]
python scripts/generate_models.py
```

### Tools

Tools use a resource-first naming convention (`resource.verb`) with category tags for discoverability.

#### App Tools
- **reviews.list**: List customer reviews with filters (`rating`, `territory`, `appStoreVersion`).
- **reviews.search**: Advanced search with rating ranges, territory matching, date windows, and content search.
- **reviews.get**: Get detailed review information.

#### TestFlight Tools
- **crashes.list**: List crash submissions from beta testers with filters (`device_model`, `os_version`, `app_platform`, `device_platform`, `build_id`, `tester_id`).
- **crashes.search**: Advanced search with:
  - Server‑side filters (`appPlatform`, `deviceModel`, `osVersion`)
  - Post‑filters: OS ranges (min/max), device model substrings (e.g., "iPhone 15"), and date windows (`created_since_days`, `created_after`, `created_before`).
- **crashes.get_by_id**: Get detailed information about a specific crash submission.
- **crashes.get_log**: Retrieve the raw crash log text for a specific submission.

### Architecture
- `src/app_store_connect_mcp/server.py`: MCP stdio server entrypoint
- `src/app_store_connect_mcp/core/`: Core architectural components
  - `protocols.py`: Abstract interfaces (APIClient, DomainHandler)
  - `base_handler.py`: Abstract base class for domain handlers
  - `query_builder.py`: Fluent API query construction with pagination
  - `filters.py`: Chainable post‑processing filter engine
  - `response_handler.py`: Standardized API response processing
  - `container.py`: Dependency injection container
  - `errors.py`: Structured error handling
- `src/app_store_connect_mcp/clients/`: API client implementations
  - `app_store_connect.py`: Async App Store Connect client with JWT auth
  - `http_client.py`: Base HTTP client with error handling
- `src/app_store_connect_mcp/domains/`: Domain‑specific implementations
  - `testflight/handlers.py`: TestFlight crash management tools
  - `app/handlers.py`: App Store review management tools
- `src/app_store_connect_mcp/models/app_store_connect_models.py`: Auto‑generated Pydantic v2 models from OpenAPI spec
- `scripts/generate_models.py`: Fetches Apple's OpenAPI spec and generates type‑safe models
- `app_store_connect_api_openapi.json`: Apple's OpenAPI spec (checked in for reliability)

### Credits
Built on the official Model Context Protocol Python SDK — see the docs and examples in the
[python‑sdk README](https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file).