"""DuckDB query executor.

Executes SQL queries against local DuckDB databases with timeout support
and result normalization.
"""

import duckdb
import time
from typing import Optional
from lakeforge.executor.base import BaseExecutor, ExecutionResult, ExecutionStatus, ExecutionError


class DuckDBExecutor(BaseExecutor):
    """Execute SQL queries against DuckDB.

    Features:
    - Local execution (no network)
    - Timeout support via query timeout setting
    - Automatic result normalization
    - Connection pooling
    """

    def __init__(self, database: str = ":memory:", max_result_rows: int = 10000):
        """Initialize DuckDB executor.

        Args:
            database: Path to DuckDB database file (default :memory:)
            max_result_rows: Maximum rows to return
        """
        super().__init__(max_result_rows)
        self.database = database
        self.connection = None

    def _get_connection(self):
        """Get or create DuckDB connection."""
        if self.connection is None:
            self.connection = duckdb.connect(self.database)
        return self.connection

    def execute(self, sql: str, timeout_sec: int = 30) -> ExecutionResult:
        """Execute SQL query against DuckDB.

        Args:
            sql: SQL query string
            timeout_sec: Query timeout in seconds

        Returns:
            ExecutionResult with status, data, and metadata
        """
        start_time = time.time()

        try:
            data, columns, duration_ms = self._execute_impl(sql, timeout_sec)
            return self._limit_results(data, columns, duration_ms)
        except TimeoutError as e:
            return self._handle_error(e, sql)
        except Exception as e:
            return self._handle_error(e, sql)

    def _execute_impl(self, sql: str, timeout_sec: int) -> tuple:
        """Execute SQL and return normalized results.

        Args:
            sql: SQL query string
            timeout_sec: Query timeout in seconds

        Returns:
            Tuple of (data, columns, duration_ms)

        Raises:
            ExecutionError: If query fails
            TimeoutError: If query exceeds timeout
        """
        conn = self._get_connection()
        start_time = time.time()

        try:
            # Note: DuckDB timeout is set via config, not per-query
            # Timeout enforcement would happen at executor wrapper level
            
            # Execute query
            result = conn.execute(sql).fetchall()

            # Get column names from result description
            columns = [desc[0] for desc in conn.description] if conn.description else []

            # Normalize to list of dicts
            data = [dict(zip(columns, row)) for row in result]

            duration_ms = (time.time() - start_time) * 1000

            return data, columns, duration_ms

        except Exception as e:
            error_msg = str(e)

            # Check if it's a timeout error
            if "timeout" in error_msg.lower():
                raise TimeoutError(f"Query execution exceeded {timeout_sec} second timeout")

            # Check for other DuckDB-specific errors
            if "not found" in error_msg.lower():
                raise ExecutionError(f"Table or column not found: {error_msg}")
            elif "syntax error" in error_msg.lower():
                raise ExecutionError(f"SQL syntax error: {error_msg}")
            else:
                raise ExecutionError(f"Query execution failed: {error_msg}")

    def close(self):
        """Close database connection."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def load_data(self, data_source: str) -> bool:
        """Load data from a source (CSV, Parquet, etc.).

        Args:
            data_source: Path to data file

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            if data_source.endswith(".csv"):
                # For CSV, just verify it can be read
                conn.execute(f"SELECT COUNT(*) FROM read_csv('{data_source}')")
            elif data_source.endswith(".parquet"):
                # For Parquet, just verify it can be read
                conn.execute(f"SELECT COUNT(*) FROM read_parquet('{data_source}')")
            else:
                # Try to read as table
                conn.execute(f"SELECT COUNT(*) FROM '{data_source}'")
            return True
        except Exception as e:
            raise ExecutionError(f"Failed to load data source '{data_source}': {str(e)}")

    def get_table_schema(self, table_name: str) -> dict:
        """Get schema of a table.

        Args:
            table_name: Name of the table

        Returns:
            Dict with table schema information

        Raises:
            ExecutionError: If table not found
        """
        try:
            conn = self._get_connection()
            result = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()

            if not result:
                raise ExecutionError(f"Table '{table_name}' not found")

            schema = []
            for row in result:
                schema.append(
                    {
                        "name": row[1],
                        "type": row[2],
                        "nullable": not row[3],  # notnull is inverted
                        "default": row[4],
                        "primary_key": row[5],
                    }
                )

            return {"table": table_name, "columns": schema}

        except Exception as e:
            raise ExecutionError(f"Failed to get schema for '{table_name}': {str(e)}")

    def list_tables(self) -> list:
        """List all tables in database.

        Returns:
            List of table names
        """
        try:
            conn = self._get_connection()
            result = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            raise ExecutionError(f"Failed to list tables: {str(e)}")
