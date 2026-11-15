"""SQLite connector for Lakeforge."""

import sqlite3
from typing import Any
import logging

from lakeforge.sources.registry import BaseConnector

logger = logging.getLogger(__name__)


class SQLiteConnector(BaseConnector):
    """Connector for SQLite databases."""

    def __init__(self, database_path: str, source: str = None):
        """Initialize SQLite connector.

        Args:
            database_path: Path to SQLite database file (.db or .sqlite)
            source: Source URI (for metadata)
        """
        self.database_path = database_path
        self.source = source or f"sqlite:///{database_path}"
        self.connection = None

    def connect(self) -> Any:
        """Establish connection to SQLite.

        Returns:
            SQLite connection object.

        Raises:
            Exception: If connection fails.
        """
        try:
            self.connection = sqlite3.connect(self.database_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite at {self.database_path}")
            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {str(e)}")
            raise

    def close(self) -> None:
        """Close SQLite connection."""
        if self.connection:
            self.connection.close()
            logger.info("SQLite connection closed")

    def list_tables(self) -> list[str]:
        """List all tables in the database.

        Returns:
            List of table names (excluding sqlite_* system tables).
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            logger.debug(f"Found {len(tables)} tables")
            return tables
        finally:
            cursor.close()

    def get_schema(self, table_name: str) -> dict[str, str]:
        """Get column schema for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Dict mapping column name to data type.
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            # PRAGMA returns: (cid, name, type, notnull, dflt_value, pk)
            schema = {row[1]: row[2] for row in cursor.fetchall()}
            logger.debug(f"Schema for {table_name}: {len(schema)} columns")
            return schema
        finally:
            cursor.close()

    def get_row_count(self, table_name: str) -> int:
        """Get row count for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Exact row count.
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            logger.debug(f"Row count for {table_name}: {count}")
            return count
        finally:
            cursor.close()

    def query(self, sql: str, limit: int = 1000) -> list[dict[str, Any]]:
        """Execute a query and return results.

        Args:
            sql: SQL query to execute.
            limit: Maximum rows to return.

        Returns:
            List of result rows as dictionaries.
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            clean_sql = sql.strip().rstrip(";")
            # Add LIMIT if not already present
            if "LIMIT" not in clean_sql.upper():
                clean_sql = f"{clean_sql} LIMIT {limit}"

            cursor.execute(clean_sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            logger.debug(f"Query returned {len(results)} rows")
            return results
        finally:
            cursor.close()


def create_sqlite_connector(database_path: str, source_uri: str = None) -> SQLiteConnector:
    """Create a SQLite connector.

    Args:
        database_path: Path to .db or .sqlite file.
        source_uri: Optional source URI for metadata.

    Returns:
        SQLiteConnector instance.

    Example:
        >>> conn = create_sqlite_connector("mydata.db")
    """
    return SQLiteConnector(database_path, source=source_uri)
