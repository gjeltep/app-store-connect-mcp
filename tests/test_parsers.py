"""Tests for concrete parser implementations."""

from datetime import UTC

from app_store_connect_mcp.utils.parsers import (
    parse_datetime,
    parse_version,
    version_ge,
    version_le,
)


class TestVersionParser:
    """Test version parsing utilities."""

    def test_parse_version_full(self):
        """Test parsing full semantic version."""
        assert parse_version("1.2.3") == (1, 2, 3)

    def test_parse_version_partial(self):
        """Test parsing partial versions."""
        assert parse_version("1.2") == (1, 2, 0)
        assert parse_version("1") == (1, 0, 0)

    def test_parse_version_invalid(self):
        """Test parsing invalid versions."""
        assert parse_version("abc.def.ghi") == (0, 0, 0)
        assert parse_version(None) == (0, 0, 0)

    def test_version_comparisons(self):
        """Test version comparison functions."""
        assert version_ge("2.0.0", "1.0.0") is True
        assert version_ge("1.0.0", "1.0.0") is True
        assert version_ge("0.9.0", "1.0.0") is False

        assert version_le("1.0.0", "2.0.0") is True
        assert version_le("1.0.0", "1.0.0") is True
        assert version_le("1.0.0", "0.9.0") is False


class TestDateTimeParser:
    """Test datetime parsing utilities."""

    def test_parse_datetime_valid(self):
        """Test parsing valid datetime formats."""
        # ISO with UTC
        dt = parse_datetime("2024-01-15T10:30:00+00:00")
        assert dt is not None
        assert dt.year == 2024
        assert dt.hour == 10
        assert dt.tzinfo == UTC

        # Z suffix (also UTC)
        dt = parse_datetime("2024-01-15T10:30:00Z")
        assert dt is not None
        assert dt.tzinfo == UTC

        # No timezone (assumes UTC)
        dt = parse_datetime("2024-01-15T10:30:00")
        assert dt is not None
        assert dt.tzinfo == UTC

    def test_parse_datetime_invalid(self):
        """Test parsing invalid datetimes."""
        assert parse_datetime(None) is None
        assert parse_datetime("not-a-date") is None

    def test_parse_datetime_timezone_conversion(self):
        """Test timezone conversion to UTC."""
        dt = parse_datetime("2024-01-15T10:30:00-05:00")
        assert dt is not None
        assert dt.hour == 15  # 10:30 EST = 15:30 UTC
        assert dt.tzinfo == UTC
