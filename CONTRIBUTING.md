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

### Development Commands

#### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_core_abstractions.py -v

# Run a single test
pytest tests/test_core_abstractions.py::test_container_singleton -v
```

#### Code Quality

```bash
# Run linting
ruff check src/ tests/

# Run formatting check
ruff format --check src/ tests/

# Auto-fix formatting
ruff format src/ tests/
```

#### Local Development Tools

```bash
# Validate configuration without starting the server
app-store-connect-mcp-dev --env-file .env --validate-only

# Regenerate OpenAPI models from Apple's spec
python scripts/generate_models.py
```

### Release Process

#### For Maintainers

1. **Update version** across all files:
   ```bash
   python scripts/update_version.py 0.x.x
   ```

2. **Review changes**:
   ```bash
   git diff
   ```

3. **Commit and tag**:
   ```bash
   git commit -am "Release v0.x.x"
   git tag v0.x.x
   ```

4. **Push to GitHub**:
   ```bash
   git push origin main
   git push origin v0.x.x
   ```

GitHub Actions will automatically build and publish to PyPI when a version tag is pushed.

### Notes

- CLI entry points:
  - `app-store-connect-mcp` (reads real environment variables)
  - `app-store-connect-mcp-dev` (supports `--env-file` for development)


