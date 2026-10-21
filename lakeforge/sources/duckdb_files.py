"""DuckDB connector for local files and S3 Parquet."""

from pathlib import Path
from typing import Any

import duckdb

from lakeforge.sources.registry import BaseConnector


class DuckDBConnector(BaseConnector):
    """Connector for local files (CSV, Parquet, JSON) via DuckDB."""

    def __init__(self, source: str):
        """Initialize DuckDB connector.

        Args:
            source: Local file path or S3 URL.
        """
        self.source = source
        self.connection: duckdb.DuckDBPyConnection | None = None
        self.table_name: str | None = None
        self._connect()

    def _connect(self) -> None:
        """Establish DuckDB connection and load source."""
        self.connection = duckdb.connect(":memory:")

        # Load file
        file_path = Path(self.source)
        file_ext = file_path.suffix.lower() if file_path.suffix else ""

        if self.source.startswith("s3://"):
            # S3 Parquet
            self.connection.execute("INSTALL httpfs")
            self.connection.execute("LOAD httpfs")
            self.table_name = f"data_{hash(self.source) % 1000000}"
            self.connection.execute(
                f"CREATE TABLE {self.table_name} AS SELECT * FROM read_parquet('{self.source}')"
            )
        elif file_ext == ".parquet":
            self.table_name = f"data_{hash(self.source) % 1000000}"
            self.connection.execute(
                f"CREATE TABLE {self.table_name} AS SELECT * FROM read_parquet('{self.source}')"
            )
        elif file_ext == ".csv":
            self.table_name = f"data_{hash(self.source) % 1000000}"
            self.connection.execute(
                f"CREATE TABLE {self.table_name} AS SELECT * FROM read_csv_auto('{self.source}')"
            )
        elif file_ext == ".json":
            self.table_name = f"data_{hash(self.source) % 1000000}"
            self.connection.execute(
                f"CREATE TABLE {self.table_name} AS SELECT * FROM read_json_auto('{self.source}')"
            )
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Return DuckDB connection."""
        if self.connection is None:
            self._connect()
        return self.connection

    def list_tables(self) -> list[str]:
        """List all tables in DuckDB.

        Returns:
            List of table names.
        """
        if self.table_name is None:
            return []
        return [self.table_name]

    def get_schema(self, table_name: str) -> dict[str, str]:
        """Get schema (column names and types) for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Dict mapping column name to type.
        """
        if self.connection is None:
            raise RuntimeError("Not connected")

        # Get column info
        result = self.connection.execute(
            f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'"
        ).fetchall()

        schema = {row[0]: row[1] for row in result}
        return schema

    def get_row_count(self, table_name: str) -> int:
        """Get row count for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Row count.
        """
        if self.connection is None:
            raise RuntimeError("Not connected")

        result = self.connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0] if result else 0

    def query(self, sql: str, limit: int = 1000) -> list[dict[str, Any]]:
        """Execute a query and return results.

        Args:
            sql: SQL query to execute.
            limit: Max rows to return.

        Returns:
            List of result rows as dicts.
        """
        if self.connection is None:
            raise RuntimeError("Not connected")

        # Ensure LIMIT clause
        if "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT {limit}"

        result = self.connection.execute(sql).fetchall()

        # Get column names
        columns = [desc[0] for desc in self.connection.description]

        # Convert to list of dicts
        return [dict(zip(columns, row)) for row in result]

    def close(self) -> None:
        """Close DuckDB connection."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
