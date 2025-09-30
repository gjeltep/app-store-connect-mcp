"""Configuration management with secure secrets handling."""

import os
from pathlib import Path


def load_config(env_file: str | None = None) -> dict[str, str | None]:
    """Load configuration from environment variables or optional .env file.

    Args:
        env_file: Optional path to .env file. Only loads if explicitly provided
                 AND python-dotenv is installed. For development use only.

    Returns:
        Dictionary containing configuration values

    Note:
        In production, this function reads from actual environment variables.
        The env_file parameter is intended for development convenience only.
    """
    # Conditionally load .env file if explicitly requested
    if env_file:
        try:
            from dotenv import load_dotenv

            load_dotenv(env_file)
        except ImportError:
            # python-dotenv not installed - continue with system env vars
            pass

    # Read configuration from environment
    config = {
        "APP_STORE_KEY_ID": os.getenv("APP_STORE_KEY_ID"),
        "APP_STORE_ISSUER_ID": os.getenv("APP_STORE_ISSUER_ID"),
        "APP_STORE_PRIVATE_KEY_PATH": os.getenv("APP_STORE_PRIVATE_KEY_PATH"),
        "APP_STORE_APP_ID": os.getenv("APP_STORE_APP_ID"),
        "APP_STORE_KEY_TYPE": os.getenv("APP_STORE_KEY_TYPE", "team"),
        "APP_STORE_SCOPE": os.getenv("APP_STORE_SCOPE"),
        "APP_STORE_SUBJECT": os.getenv("APP_STORE_SUBJECT"),
    }

    return config


def validate_config(config: dict[str, str | None]) -> None:
    """Validate that required configuration values are present.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If required configuration values are missing
    """
    required_keys = [
        "APP_STORE_KEY_ID",
        "APP_STORE_ISSUER_ID",
        "APP_STORE_PRIVATE_KEY_PATH",
    ]

    missing = [key for key in required_keys if not config.get(key)]

    if missing:
        raise ValueError(
            f"Missing required configuration: {', '.join(missing)}. "
            "Please set these environment variables or use --env-file for development."
        )

    # Validate private key path exists if provided
    private_key_path = config.get("APP_STORE_PRIVATE_KEY_PATH")
    if private_key_path and not Path(private_key_path).exists():
        raise ValueError(
            f"Private key file not found: {private_key_path}. "
            "Please check APP_STORE_PRIVATE_KEY_PATH."
        )


def redact_secrets(config: dict[str, str | None]) -> dict[str, str]:
    """Create a redacted version of config for safe logging.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary with sensitive values redacted
    """
    redacted = {}

    for key, value in config.items():
        if not value:
            redacted[key] = "<not set>"
        elif key in ["APP_STORE_KEY_ID", "APP_STORE_ISSUER_ID"]:
            # Redact but show length
            redacted[key] = f"<redacted:{len(value)} chars>"
        elif key == "APP_STORE_PRIVATE_KEY_PATH":
            # Show filename only, not full path
            redacted[key] = f"<path:{Path(value).name}>"
        else:
            redacted[key] = value

    return redacted


__all__ = ["load_config", "validate_config", "redact_secrets"]
