#!/usr/bin/env python3
"""
Update version numbers across all project files.

Usage:
    python scripts/update_version.py 0.2.0
"""

import json
import re
import sys
from pathlib import Path


def update_version(new_version: str):
    """Update version in all relevant project files."""

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        print(
            f"Error: Invalid version format '{new_version}'. Use semantic versioning (e.g., 0.1.1)"
        )
        sys.exit(1)

    project_root = Path(__file__).parent.parent

    # Update pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    content = pyproject_path.read_text()
    content = re.sub(r'^version = ".*"', f'version = "{new_version}"', content, flags=re.MULTILINE)
    pyproject_path.write_text(content)
    print(f"✓ Updated {pyproject_path.relative_to(project_root)}")

    # Update __init__.py
    init_path = project_root / "src" / "app_store_connect_mcp" / "__init__.py"
    content = init_path.read_text()
    content = re.sub(
        r'^__version__ = ".*"', f'__version__ = "{new_version}"', content, flags=re.MULTILINE
    )
    init_path.write_text(content)
    print(f"✓ Updated {init_path.relative_to(project_root)}")

    # Update server.json (both occurrences)
    server_json_path = project_root / "server.json"
    with open(server_json_path, "r") as f:
        data = json.load(f)

    data["version"] = new_version
    if "packages" in data and len(data["packages"]) > 0:
        data["packages"][0]["version"] = new_version

    with open(server_json_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")  # Add trailing newline
    print(f"✓ Updated {server_json_path.relative_to(project_root)}")

    print(f"\nVersion updated to {new_version} in all files.")
    print("\nNext steps:")
    print("1. Review changes: git diff")
    print("2. Commit: git commit -am 'Release v{new_version}'")
    print("3. Tag: git tag v{new_version}")
    print("4. Push: git push && git push --tags")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/update_version.py <version>")
        print("Example: python scripts/update_version.py 0.2.0")
        sys.exit(1)

    update_version(sys.argv[1])
