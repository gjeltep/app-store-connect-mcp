## Contributing

Thanks for helping improve App Store Connect MCP.

### Prerequisites

- Python 3.12+
- `uv` (recommended) or `pip`

### Setup

```bash
git clone https://github.com/gjeltep/app-store-connect-mcp.git
cd app-store-connect-mcp
uv pip install -e ".[dev]"
```

### Running tests

```bash
pytest tests/ -v

# Run a specific test file
pytest tests/test_core_abstractions.py -v

# Run a single test
pytest tests/test_core_abstractions.py::test_container_singleton -v
```

### Linting and formatting

```bash
# Lint
ruff check src/ tests/

# Check formatting
ruff format --check src/ tests/

# Apply formatting
ruff format src/ tests/
```

### Local validation and tooling

```bash
# Validate configuration without starting the server
app-store-connect-mcp-dev --env-file .env --validate-only

# Regenerate OpenAPI models
python scripts/generate_models.py
```

### Notes

- CLI entry points:
  - `app-store-connect-mcp` (reads real environment variables)
  - `app-store-connect-mcp-dev` (supports `--env-file` for development)


