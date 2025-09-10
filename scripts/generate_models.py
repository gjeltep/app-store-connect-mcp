#!/usr/bin/env python3
"""
Generate Pydantic models from the App Store Connect OpenAPI JSON spec.

Usage:
  # Install dev deps
  uv pip install -e .[dev]

  # Provide a JSON URL (required) and run
  APP_STORE_CONNECT_OPENAPI_URL="https://example.com/app_store_connect_api_openapi.json" \
    python scripts/generate_models.py

Notes:
- We fetch the JSON to a temp file (nothing is written to the repo).
- If you prefer a local file, set APP_STORE_CONNECT_OPENAPI_PATH instead of URL.
"""

import os
import subprocess
import sys
import urllib.request
import tempfile


def main() -> int:
    repo_root = os.path.dirname(os.path.dirname(__file__))
    json_path = os.getenv("APP_STORE_CONNECT_OPENAPI_PATH")

    # # Local file path flow
    if json_path:
        spec_path = json_path
        if not os.path.exists(spec_path):
            print(f"ERROR: Local spec not found: {spec_path}")
            return 1
        out_dir = os.path.join(repo_root, "src", "app_store_connect_mcp", "models")
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, "app_store_connect_models.py")

        cmd = [
            sys.executable,
            "-m",
            "datamodel_code_generator",
            "--input",
            spec_path,
            "--input-file-type",
            "openapi",
            "--target-python-version",
            "3.12",
            "--output",
            out_file,
            "--enum-field-as-literal",
            "all",
            "--output-model-type",
            "pydantic_v2.BaseModel",
        ]
        print("Running:", " ".join(cmd))
        return subprocess.call(cmd)
    # Default to Apple's public ZIP if nothing provided
    else:
        json_url = "https://developer.apple.com/sample-code/app-store-connect/app-store-connect-openapi-specification.zip"
        with tempfile.TemporaryDirectory() as td:
            out_dir = os.path.join(repo_root, "src", "app_store_connect_mcp", "models")
            os.makedirs(out_dir, exist_ok=True)
            out_file = os.path.join(out_dir, "app_store_connect_models.py")

            # If URL ends with .zip, download and extract JSON
            if json_url.lower().endswith(".zip"):
                zip_path = os.path.join(td, "spec.zip")
                print(f"Fetching OpenAPI ZIP from: {json_url}")
                try:
                    urllib.request.urlretrieve(json_url, zip_path)
                except Exception as e:
                    print(f"Failed to fetch ZIP: {e}")
                    return 1
                extract_dir = os.path.join(td, "extracted")
                os.makedirs(extract_dir, exist_ok=True)
                with tempfile.TemporaryDirectory() as _tmp:
                    pass
                import zipfile

                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(extract_dir)
                # pick the expected filename or first .json
                from pathlib import Path

                candidates = list(Path(extract_dir).rglob("*.json"))
                spec_json = None
                for p in candidates:
                    if p.name == "app_store_connect_api_openapi.json":
                        spec_json = p
                        break
                if spec_json is None and candidates:
                    spec_json = candidates[0]
                if not spec_json:
                    print("No JSON spec found inside ZIP.")
                    return 1
                spec_path = str(spec_json)
            else:
                # Fetch plain JSON
                spec_path = os.path.join(td, "spec.json")
                print(f"Fetching OpenAPI JSON from: {json_url}")
                try:
                    urllib.request.urlretrieve(json_url, spec_path)
                except Exception as e:
                    print(f"Failed to fetch JSON spec: {e}")
                    return 1

            cmd = [
                sys.executable,
                "-m",
                "datamodel_code_generator",
                "--input",
                spec_path,
                "--input-file-type",
                "openapi",
                "--target-python-version",
                "3.12",
                "--output",
                out_file,
                "--enum-field-as-literal",
                "all",
                "--output-model-type",
                "pydantic_v2.BaseModel",
            ]
            print("Running:", " ".join(cmd))
            return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
