"""Databricks SQL connector using databricks-sql-connector library."""

import os
from typing import Any
from urllib.parse import urlparse

from lakeforge.sources.registry import BaseConnector


class DatabricksConnector(BaseConnector):
    """Connector for Databricks SQL via databricks-sql-connector."""

    def __init__(self, source: str):
        """Initialize Databricks connector.

        Args:
            source: Databricks URI (databricks://workspace/catalog/schema/table)

        Raises:
            ImportError: If databricks-sql-connector is not installed.
            ValueError: If authentication token is not available.
        """
        try:
            import databricks.sql
        except ImportError:
            raise ImportError(
                "Databricks connector requires: pip install databricks-sql-connector"
            )

        self.source = source
        self.connection: Any = None
        self.workspace_id: str = ""
        self.catalog_name: str = ""
        self.schema_name: str = ""
        self.table_name: str = ""

        self._parse_uri()
        self._connect()

    def _parse_uri(self) -> None:
        """Parse Databricks URI.

        Format: databricks://workspace_id/catalog/schema/table
        or: databricks://workspace_id.cloud.databricks.com/catalog/schema/table
        """
        parsed = urlparse(self.source)
        
        # Extract workspace and path
        netloc = parsed.netloc  # workspace_id or workspace_id.cloud.databricks.com
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) < 1:
            raise ValueError(
                f"Invalid Databricks URI: {self.source}. "
                "Expected: databricks://workspace/catalog/schema/table"
            )

        # For simplicity, use netloc as workspace ID
        self.workspace_id = netloc.split(".")[0]  # Extract workspace_id from FQDN if needed

        # Parse catalog, schema, table
        if len(path_parts) >= 3:
            self.catalog_name = path_parts[0]
            self.schema_name = path_parts[1]
            self.table_name = path_parts[2]
        else:
            raise ValueError(
                f"Invalid Databricks URI: {self.source}. "
                "Expected: databricks://workspace/catalog/schema/table"
            )

    def _connect(self) -> None:
        """Establish connection to Databricks SQL.

        Raises:
            ValueError: If authentication token is not available.
        """
        import databricks.sql

        # Get authentication token
        token = os.getenv("DATABRICKS_TOKEN")
        if not token:
            raise ValueError(
                "Databricks authentication token not found. "
                "Set DATABRICKS_TOKEN environment variable."
            )

        # Get host (optional, can be inferred from workspace_id)
        host = os.getenv("DATABRICKS_HOST", f"{self.workspace_id}.cloud.databricks.com")

        try:
            self.connection = databricks.sql.connect(
                host=host,
                http_path="/sql/1.0/warehouses/default",  # Default warehouse
                token=token,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Databricks: {e}")

    def connect(self) -> Any:
        """Return Databricks connection."""
        if self.connection is None:
            self._connect()
        return self.connection

    def list_tables(self) -> list[str]:
        """List all tables in catalog.schema.

        Returns:
            List of table names.
        """
        if self.connection is None:
            raise RuntimeError("Not connected")

        try:
            cursor = self.connection.cursor()
            query = (
                f"SELECT table_name FROM {self.catalog_name}.information_schema.tables "
                f"WHERE table_schema = '{self.schema_name}'"
            )
            cursor.execute(query)
            results = cursor.fetchall()
            return [row[0] for row in results]
        except Exception as e:
            raise RuntimeError(f"Failed to list tables: {e}")

    def get_schema(self, table_name: str) -> dict[str, str]:
        """Get schema (column names and types) for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Dict mapping column name to type.

        Raises:
            RuntimeError: If query fails.
        """
        if self.connection is None:
            raise RuntimeError("Not connected")

        try:
            cursor = self.connection.cursor()
            full_name = f"{self.catalog_name}.{self.schema_name}.{table_name}"
            query = f"DESC TABLE {full_name}"
            cursor.execute(query)
            results = cursor.fetchall()

            # DESC TABLE returns (col_name, col_type, ...)
            schema = {row[0]: row[1] for row in results}
            return schema
        except Exception as e:
            raise RuntimeError(f"Failed to get schema for {table_name}: {e}")

    def get_row_count(self, table_name: str) -> int:
        """Get approximate row count for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Row count.

        Raises:
            RuntimeError: If query fails.
        """
        if self.connection is None:
            raise RuntimeError("Not connected")

        try:
            cursor = self.connection.cursor()
            full_name = f"{self.catalog_name}.{self.schema_name}.{table_name}"
            query = f"SELECT COUNT(*) as count FROM {full_name}"
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            raise RuntimeError(f"Failed to get row count for {table_name}: {e}")

    def query(self, sql: str, limit: int = 1000) -> list[dict[str, Any]]:
        """Execute a query and return results.

        Args:
            sql: SQL query to execute.
            limit: Max rows to return.

        Returns:
            List of result rows as dicts.

        Raises:
            RuntimeError: If query fails.
        """
        if self.connection is None:
            raise RuntimeError("Not connected")

        try:
            cursor = self.connection.cursor()
            
            # Add LIMIT if not present
            if "LIMIT" not in sql.upper():
                sql = f"{sql} LIMIT {limit}"

            cursor.execute(sql)
            
            # Fetch column names
            column_names = [desc[0] for desc in cursor.description]
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            results = []
            for row in rows:
                results.append({column_names[i]: row[i] for i in range(len(column_names))})
            
            return results
        except Exception as e:
            raise RuntimeError(f"Query failed: {e}")

    def close(self) -> None:
        """Close connection to Databricks."""
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None
