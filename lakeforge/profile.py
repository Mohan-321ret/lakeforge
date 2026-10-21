"""L2 Profiling: Column statistics and sampling."""

import time
from typing import Any, Optional

from lakeforge.pii import PIIDetector, PIIMasker, PIIMaskingMethod


class Sampler:
    """Sample rows from a table with caps."""

    def __init__(
        self,
        max_rows: int = 1000,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        timeout_sec: int = 30,
    ):
        """Initialize sampler.

        Args:
            max_rows: Maximum rows to sample.
            max_bytes: Maximum bytes to sample (approximate).
            timeout_sec: Timeout per table sample.
        """
        self.max_rows = max_rows
        self.max_bytes = max_bytes
        self.timeout_sec = timeout_sec

    def sample_from_connector(self, connector, table_name: str) -> list[dict[str, Any]]:
        """Sample rows from a table via connector.

        Args:
            connector: Source connector.
            table_name: Table name.

        Returns:
            List of sampled rows as dicts.
        """
        start_time = time.time()

        try:
            # Query with LIMIT
            sql = f"SELECT * FROM {table_name} LIMIT {self.max_rows}"
            results = connector.query(sql, limit=self.max_rows)

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > self.timeout_sec:
                print(f"⚠ Sampling timeout ({elapsed:.1f}s > {self.timeout_sec}s)")

            return results
        except Exception as e:
            print(f"⚠ Sampling failed for {table_name}: {str(e)}")
            return []


class StatCalculator:
    """Calculate column statistics."""

    def __init__(self):
        """Initialize stat calculator."""
        pass

    def calculate_column_stats(
        self, column_name: str, column_type: str, sample_values: list[Any]
    ) -> dict[str, Any]:
        """Calculate statistics for a column.

        Args:
            column_name: Column name.
            column_type: Column type.
            sample_values: Sample values from column.

        Returns:
            Dict of statistics.
        """
        stats = {
            "null_count": 0,
            "null_rate": 0.0,
            "unique_count": 0,
            "unique_rate": 0.0,
            "min_value": None,
            "max_value": None,
            "top_values": [],
        }

        if not sample_values:
            return stats

        # Filter out nulls
        non_null_values = [v for v in sample_values if v is not None and v != ""]
        null_count = len(sample_values) - len(non_null_values)

        stats["null_count"] = null_count
        stats["null_rate"] = null_count / len(sample_values) if sample_values else 0.0
        stats["unique_count"] = len(set(non_null_values))
        stats["unique_rate"] = stats["unique_count"] / len(non_null_values) if non_null_values else 0.0

        # Min/max for numeric/date types
        if column_type in ("BIGINT", "INTEGER", "FLOAT", "DOUBLE", "DATE", "TIMESTAMP"):
            try:
                numeric_values = [v for v in non_null_values if v is not None]
                if numeric_values:
                    stats["min_value"] = str(min(numeric_values))
                    stats["max_value"] = str(max(numeric_values))
            except (TypeError, ValueError):
                pass

        # Top values (most common)
        if non_null_values:
            value_counts = {}
            for v in non_null_values:
                value_counts[str(v)] = value_counts.get(str(v), 0) + 1

            top_n = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["top_values"] = [{"value": v, "count": c} for v, c in top_n]

        return stats


class ColumnProfile:
    """Profile for a single column."""

    def __init__(
        self,
        name: str,
        type: str,
        nullable: bool,
        sample_values: list[Any],
    ):
        """Initialize column profile.

        Args:
            name: Column name.
            type: Column type.
            nullable: Whether column allows nulls.
            sample_values: Sample values.
        """
        self.name = name
        self.type = type
        self.nullable = nullable
        self.sample_values = sample_values

        # Calculate stats
        self.stat_calculator = StatCalculator()
        self.stats = self.stat_calculator.calculate_column_stats(
            name, type, sample_values
        )

        # Detect PII
        self.pii_detector = PIIDetector()
        self.is_pii, self.pii_type, self.pii_confidence = self.pii_detector.analyze_column(
            name, sample_values
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict representation.
        """
        return {
            "name": self.name,
            "type": self.type,
            "nullable": self.nullable,
            "is_pii": self.is_pii,
            "pii_type": self.pii_type,
            "pii_confidence": self.pii_confidence,
            "stats": self.stats,
        }


class L2Profile:
    """L2 Profile with statistics and PII detection."""

    def __init__(self, source: str, masking_method: str = "hash"):
        """Initialize L2 profile.

        Args:
            source: Source URI.
            masking_method: PII masking method (hash or redact).
        """
        self.source = source
        self.tables: dict[str, "TableProfile"] = {}
        self.masking_method = PIIMaskingMethod(masking_method)
        self.masker = PIIMasker(self.masking_method)
        self.audit_log: list[dict[str, Any]] = []

    def add_table_profile(self, table_profile: "TableProfile") -> None:
        """Add table profile.

        Args:
            table_profile: TableProfile object.
        """
        self.tables[table_profile.name] = table_profile

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict representation.
        """
        return {
            "source": self.source,
            "tables": {
                name: table.to_dict() for name, table in self.tables.items()
            },
        }


class TableProfile:
    """Profile for a single table."""

    def __init__(
        self,
        name: str,
        row_count: int,
        sample_count: int,
    ):
        """Initialize table profile.

        Args:
            name: Table name.
            row_count: Total rows in table.
            sample_count: Number of sampled rows.
        """
        self.name = name
        self.row_count = row_count
        self.sample_count = sample_count
        self.columns: dict[str, ColumnProfile] = {}
        self.pii_columns: dict[str, Optional[str]] = {}  # col_name -> pii_type

    def add_column_profile(self, col_profile: ColumnProfile) -> None:
        """Add column profile.

        Args:
            col_profile: ColumnProfile object.
        """
        self.columns[col_profile.name] = col_profile
        if col_profile.is_pii:
            self.pii_columns[col_profile.name] = col_profile.pii_type

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict representation.
        """
        return {
            "name": self.name,
            "row_count": self.row_count,
            "sample_count": self.sample_count,
            "columns": {
                name: col.to_dict() for name, col in self.columns.items()
            },
            "pii_columns": self.pii_columns,
        }
