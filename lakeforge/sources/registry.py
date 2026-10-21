"""Source connector registry and factory."""

from abc import ABC, abstractmethod
from typing import Any, Optional

import duckdb


class BaseConnector(ABC):
    """Abstract base class for data source connectors."""

    @abstractmethod
    def connect(self) -> Any:
        """Establish connection to source."""
        pass

    @abstractmethod
    def list_tables(self) -> list[str]:
        """List all tables in source."""
        pass

    @abstractmethod
    def get_schema(self, table_name: str) -> dict[str, str]:
        """Get schema (column names and types) for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Dict mapping column name to type.
        """
        pass

    @abstractmethod
    def get_row_count(self, table_name: str) -> int:
        """Get approximate row count for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Row count.
        """
        pass

    @abstractmethod
    def query(self, sql: str, limit: int = 1000) -> list[dict[str, Any]]:
        """Execute a query and return results.

        Args:
            sql: SQL query to execute.
            limit: Max rows to return.

        Returns:
            List of result rows as dicts.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close connection to source."""
        pass


def get_connector(source: str) -> BaseConnector:
    """Factory function to get appropriate connector for a source.

    Args:
        source: Source URI:
            - Local files: data.csv, data.parquet, data.json
            - S3: s3://bucket/key
            - Databricks: databricks://workspace/catalog/schema/table
            - PostgreSQL: postgres://user:pass@host:port/database
            - MySQL: mysql://user:pass@host:port/database
            - SQL Server: mssql://user:pass@host:port/database
            - Oracle: oracle://user:pass@host:port/sid
            - SQLite: sqlite:///path/to/database.db

    Returns:
        Appropriate BaseConnector implementation.

    Raises:
        ValueError: If source type is not recognized.
    """
    # S3 or local file → DuckDB
    if source.startswith("s3://") or "://" not in source:
        from lakeforge.sources.duckdb_files import DuckDBConnector

        return DuckDBConnector(source)

    # Databricks
    if source.startswith("databricks://"):
        try:
            from lakeforge.sources.databricks_sql import DatabricksConnector

            return DatabricksConnector(source)
        except ImportError:
            raise ValueError(
                "Databricks connector requires: pip install lakeforge[databricks]"
            )

    # PostgreSQL
    if source.startswith("postgres://"):
        try:
            from lakeforge.sources.postgres import PostgresConnector

            return PostgresConnector(source)
        except ImportError:
            raise ValueError(
                "Postgres connector requires: pip install sqlalchemy psycopg2-binary"
            )

    # MySQL / MariaDB
    if source.startswith("mysql://"):
        try:
            from lakeforge.sources.mysql import create_mysql_connector

            return create_mysql_connector(source)
        except ImportError:
            raise ValueError(
                "MySQL connector requires: pip install mysql-connector-python"
            )

    # Microsoft SQL Server
    if source.startswith("mssql://") or source.startswith("sqlserver://"):
        try:
            from lakeforge.sources.sqlserver import create_sqlserver_connector

            return create_sqlserver_connector(source)
        except ImportError:
            raise ValueError(
                "SQL Server connector requires: pip install pyodbc"
            )

    # Oracle Database
    if source.startswith("oracle://"):
        try:
            from lakeforge.sources.oracle import create_oracle_connector

            return create_oracle_connector(source)
        except ImportError:
            raise ValueError(
                "Oracle connector requires: pip install oracledb"
            )

    # SQLite
    if source.startswith("sqlite://"):
        from lakeforge.sources.sqlite import create_sqlite_connector

        # Strip scheme: sqlite:///path -> path (Windows-safe, keeps drive letter)
        remainder = source[len("sqlite://"):]
        if remainder.startswith("/") and len(remainder) > 2 and remainder[2] == ":":
            # Windows path like sqlite:///c:/... -> c:/...
            db_path = remainder[1:]
        else:
            db_path = remainder
        return create_sqlite_connector(db_path, source_uri=source)

    raise ValueError(
        f"Unknown source type: {source}\n"
        f"Supported schemes: s3://, databricks://, postgres://, mysql://, "
        f"mssql://, oracle://, sqlite://, or local file path"
    )
