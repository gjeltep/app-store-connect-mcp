"""Command-line interface for development use with --env-file support."""

import argparse
import sys

from app_store_connect_mcp.config import load_config, redact_secrets, validate_config


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="App Store Connect MCP Server (Development Mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load config from .env file
  %(prog)s --env-file .env

  # Load config from custom location
  %(prog)s --env-file /path/to/my.env

Note:
  This CLI is for DEVELOPMENT use only. In production, use the main
  entry point which reads from actual environment variables:
    app-store-connect-mcp
        """,
    )

    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to .env file for loading configuration (development only)",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate configuration without starting the server",
    )

    return parser.parse_args()


def cli_main() -> None:
    """CLI entry point for development with --env-file support."""
    args = parse_args()

    # Load configuration
    try:
        config = load_config(env_file=args.env_file)
        validate_config(config)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # If validation only, print redacted config and exit
    if args.validate_only:
        print("Configuration validation successful!")
        print("\nRedacted configuration:")
        for key, value in redact_secrets(config).items():
            print(f"  {key}: {value}")
        sys.exit(0)

    # Start the server with validated configuration
    print("Starting App Store Connect MCP server...")
    if args.env_file:
        print(f"Loaded configuration from: {args.env_file}")

    # Import and run the server
    from app_store_connect_mcp.server import main

    main()


if __name__ == "__main__":
    cli_main()


__all__ = ["cli_main"]
