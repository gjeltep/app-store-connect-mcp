"""Utility parsers for version and datetime handling."""

from typing import Optional, Tuple
from datetime import datetime, timezone


def parse_version(value: str) -> Tuple[int, int, int]:
    """Parse version string into (major, minor, patch)."""
    parts = (value or "").split(".")
    major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    return major, minor, patch


def version_ge(a: str, b: str) -> bool:
    """Check if version a >= version b."""
    return parse_version(a) >= parse_version(b)


def version_le(a: str, b: str) -> bool:
    """Check if version a <= version b."""
    return parse_version(a) <= parse_version(b)


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object."""
    if not value:
        return None
    # Accept trailing 'Z' by converting to +00:00
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None
