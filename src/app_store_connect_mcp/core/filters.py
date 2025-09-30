"""Reusable filter engine for post-processing API responses."""

from datetime import UTC, datetime, timedelta
from typing import Any

from app_store_connect_mcp.utils.parsers import parse_datetime, version_ge, version_le


class FilterEngine:
    """Engine for applying filters to collections of data."""

    def __init__(self, data: list[dict[str, Any]]):
        """Initialize the filter engine with data.

        Args:
            data: List of dictionaries to filter
        """
        self.data = data

    def apply(self) -> list[dict[str, Any]]:
        """Return the filtered data.

        Returns:
            The filtered list of dictionaries
        """
        return self.data

    def filter_by_date_range(
        self,
        field_path: str,
        after: str | None = None,
        before: str | None = None,
        since_days: int | None = None,
    ) -> "FilterEngine":
        """Filter items by date range.

        Args:
            field_path: Dot-separated path to the date field (e.g., "attributes.createdDate")
            after: ISO-8601 datetime string for minimum date (inclusive)
            before: ISO-8601 datetime string for maximum date (inclusive)
            since_days: Number of days from now to include (alternative to after)

        Returns:
            Self for method chaining
        """
        if not any([after, before, since_days]):
            return self

        # Calculate date boundaries
        now_utc = datetime.now(UTC)
        min_dt: datetime | None = None
        max_dt: datetime | None = None

        if since_days and since_days > 0:
            min_dt = now_utc - timedelta(days=since_days)

        if after:
            parsed_after = parse_datetime(after)
            if parsed_after:
                min_dt = parsed_after if not min_dt else max(min_dt, parsed_after)

        if before:
            max_dt = parse_datetime(before)

        def matches(item: dict[str, Any]) -> bool:
            value = self._get_nested_value(item, field_path)
            if not value:
                return False

            item_dt = parse_datetime(value) if isinstance(value, str) else value
            if not item_dt:
                return False

            if min_dt and item_dt < min_dt:
                return False
            if max_dt and item_dt > max_dt:
                return False

            return True

        self.data = [item for item in self.data if matches(item)]
        return self

    def filter_by_text_contains(
        self,
        field_path: str,
        search_terms: list[str] | None,
        case_sensitive: bool = False,
    ) -> "FilterEngine":
        """Filter items where field contains any of the search terms.

        Args:
            field_path: Dot-separated path to the text field
            search_terms: List of terms to search for (OR condition)
            case_sensitive: Whether to perform case-sensitive matching

        Returns:
            Self for method chaining
        """
        if not search_terms:
            return self

        def matches(item: dict[str, Any]) -> bool:
            value = self._get_nested_value(item, field_path)
            if not value:
                return False

            text = str(value)
            if not case_sensitive:
                text = text.lower()
                terms = [term.lower() for term in search_terms]
            else:
                terms = search_terms

            return any(term in text for term in terms)

        self.data = [item for item in self.data if matches(item)]
        return self

    def filter_by_numeric_range(
        self,
        field_path: str,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> "FilterEngine":
        """Filter items by numeric range.

        Args:
            field_path: Dot-separated path to the numeric field
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)

        Returns:
            Self for method chaining
        """
        if min_value is None and max_value is None:
            return self

        def matches(item: dict[str, Any]) -> bool:
            value = self._get_nested_value(item, field_path)
            if value is None:
                return False

            try:
                num_value = float(value)
            except (TypeError, ValueError):
                return False

            if min_value is not None and num_value < min_value:
                return False
            if max_value is not None and num_value > max_value:
                return False

            return True

        self.data = [item for item in self.data if matches(item)]
        return self

    def filter_by_version_range(
        self,
        field_path: str,
        min_version: str | None = None,
        max_version: str | None = None,
    ) -> "FilterEngine":
        """Filter items by version string range.

        Args:
            field_path: Dot-separated path to the version field
            min_version: Minimum version (inclusive)
            max_version: Maximum version (inclusive)

        Returns:
            Self for method chaining
        """
        if not min_version and not max_version:
            return self

        def matches(item: dict[str, Any]) -> bool:
            value = self._get_nested_value(item, field_path)
            if not value:
                return False

            version = str(value)

            if min_version and not version_ge(version, min_version):
                return False
            if max_version and not version_le(version, max_version):
                return False

            return True

        self.data = [item for item in self.data if matches(item)]
        return self

    def filter_by_values(self, field_path: str, allowed_values: list[Any] | None) -> "FilterEngine":
        """Filter items where field matches any of the allowed values.

        Args:
            field_path: Dot-separated path to the field
            allowed_values: List of allowed values

        Returns:
            Self for method chaining
        """
        if not allowed_values:
            return self

        def matches(item: dict[str, Any]) -> bool:
            value = self._get_nested_value(item, field_path)
            return value in allowed_values

        self.data = [item for item in self.data if matches(item)]
        return self

    def limit(self, max_items: int) -> "FilterEngine":
        """Limit the number of results.

        Args:
            max_items: Maximum number of items to return

        Returns:
            Self for method chaining
        """
        if max_items > 0:
            self.data = self.data[:max_items]
        return self

    @staticmethod
    def _get_nested_value(data: dict[str, Any], path: str) -> Any:
        """Get a value from a nested dictionary using dot notation.

        Args:
            data: The dictionary to search
            path: Dot-separated path (e.g., "attributes.createdDate")

        Returns:
            The value at the path, or None if not found
        """
        keys = path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return None
            else:
                return None

        return value
