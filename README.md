## App Store Connect MCP Server

Talk to App Store Connect about your app. Modular tools, async I/O, and OpenAPI‑driven typing so your agent stays accurate as Apple evolves.

### Why this is different
- **Spec‑aware**: Fields and enums are derived from Apple’s OpenAPI spec at runtime, reducing drift and surprise breakage.
- **Fast by default**: Async `httpx` client, server‑side filtering, and smart pagination to keep payloads lean.
- **Smart filtering**: Server‑side + client‑side filtering with chainable filter engine for complex queries.
- **Modular domains**: Clean separation of tool schemas and handlers; add new domains without touching the core; optimized LLM discovery/ usage
- **MCP‑native**: Stdio transport, capability declarations, and tool wiring align with the official SDK [python‑sdk README](https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file).

### Quickstart
1) Install Dependencies

```bash
uv pip install -e .
```

2) Configure Environment

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

#### Analytics Tools
**Requests:**
- **analytics_report_requests.list**: List analytics report requests for an app with filters (`access_type`).
- **report_requests.create**: Create new analytics report requests for specific metrics and timeframes.
- **report_requests.get**: Get detailed information about a specific analytics report request.

**Reports:**
- **report_requests.list_reports**: List available reports within a request with filters (`name`, `category`).
- **reports.get**: Get specific analytics report information.
- **reports.list_instances**: List report instances with filters (`granularity`, `processing_date`).
- **report_instances.get**: Get detailed information about a specific report instance.

**Segments:**
- **report_instances.list_segments**: List data segments for a report instance.
- **report_segments.get**: Get segment download information (checksum, URL, size).
- **report_instances.download_data**: Download analytics report data to a TSV file.

#### Xcode Cloud Tools
**Products & Workflows:**
- **products.list**: List all Xcode Cloud products with filters (`product_type`).
- **products.get**: Get detailed information about a specific product.
- **workflows.list**: List workflows for a product with filters (`is_enabled`).
- **workflows.get**: Get detailed workflow information (note: create/update/delete operations not supported for safety).

**Builds:**
- **builds.list**: List builds for a product or workflow with filters (`execution_progress`, `completion_status`, `is_pull_request_build`).
- **builds.get**: Get detailed build information including status, duration, and issue counts.
- **builds.start**: Start a new build for a workflow with optional branch/tag or pull request specification.

**Build Artifacts & Results:**
- **artifacts.list**: List downloadable artifacts for a build.
- **issues.list**: List issues (errors, warnings) for builds or workflows.
- **test_results.list**: List test results including status, duration, and failure messages.

**SCM Integration:**
- **scm_providers.list**: List configured SCM providers (GitHub, GitLab, Bitbucket).
- **repositories.list**: List Git repositories for an SCM provider.
- **pull_requests.list**: List pull requests for a repository.
- **git_references.list**: List branches and tags for a repository.

### Architecture

```mermaid
graph TD
    %% Entry Point
    subgraph "Entry Point"
        SERVER[server.py<br/>MCP stdio server]
    end

    %% Domain Implementations
    subgraph "Domain Handlers"
        TESTFLIGHT[testflight/handlers.py<br/>TestFlight crash<br/>management]
        APP[app/handlers.py<br/>App Store review<br/>management]
        ANALYTICS[analytics/handlers.py<br/>Analytics report<br/>management]
        XCODE_CLOUD[xcode_cloud/handlers.py<br/>Xcode Cloud CI/CD<br/>management]
    end

    %% Core Architecture
    subgraph "Core Components"
        subgraph "Core Framework"
            PROTOCOLS[protocols.py<br/>Abstract interfaces]
            BASE_HANDLER[base_handler.py<br/>Abstract base class]
            QUERY_BUILDER[query_builder.py<br/>Fluent query construction]
            FILTERS[filters.py<br/>Chainable filter engine]
            RESPONSE_HANDLER[response_handler.py<br/>API response processing]
            CONTAINER[container.py<br/>Dependency injection]
            ERRORS[errors.py<br/>Structured error handling]
        end

        subgraph "API Layer"
            ASC_CLIENT[app_store_connect.py<br/>App Store Connect client<br/>with JWT auth]
            HTTP_CLIENT[http_client.py<br/>Base HTTP client]
            MODELS[app_store_connect_models.py<br/>Auto-generated Pydantic<br/>models from OpenAPI spec]
        end

        subgraph "Data & Tools"
            OPENAPI[app_store_connect_api_openapi.json<br/>Apple's OpenAPI spec]
            GENERATE_SCRIPT[scripts/generate_models.py<br/>Model generation script]
        end
    end

    %% Vertical Stack Relationships
    SERVER -->|"routes to"| ANALYTICS
    ANALYTICS -->|"uses"| ASC_CLIENT

    %% Styling
    classDef entry fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef core fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef domain fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class SERVER entry
    class PROTOCOLS,BASE_HANDLER,QUERY_BUILDER,FILTERS,RESPONSE_HANDLER,CONTAINER,ERRORS,ASC_CLIENT,HTTP_CLIENT,MODELS,OPENAPI,GENERATE_SCRIPT core
    class TESTFLIGHT,APP,ANALYTICS,XCODE_CLOUD domain
```

### Credits
Built on the official Model Context Protocol Python SDK — see the docs and examples in the
[python‑sdk README](https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file).