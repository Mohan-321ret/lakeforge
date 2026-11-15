"""MySQL/MariaDB connector for Lakeforge."""

from typing import Any, Optional
import logging

from lakeforge.sources.registry import BaseConnector

logger = logging.getLogger(__name__)


class MySQLConnector(BaseConnector):
    """Connector for MySQL and MariaDB databases."""

    def __init__(
        self,
        host: str,
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "",
        charset: str = "utf8mb4",
    ):
        """Initialize MySQL connector.

        Args:
            host: MySQL server hostname or IP
            port: MySQL port (default 3306)
            user: Database user
            password: Database password
            database: Default database name
            charset: Character set (default utf8mb4)
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.connection = None

    def connect(self) -> Any:
        """Establish connection to MySQL.

        Returns:
            MySQL connection object.

        Raises:
            ImportError: If mysql-connector-python not installed.
            Exception: If connection fails.
        """
        try:
            import mysql.connector
        except ImportError:
            raise ImportError(
                "mysql-connector-python not installed. "
                "Install with: pip install mysql-connector-python"
            )

        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                autocommit=True,
            )
            logger.info(f"Connected to MySQL at {self.host}:{self.port}/{self.database}")
            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            raise

    def close(self) -> None:
        """Close MySQL connection."""
        if self.connection:
            self.connection.close()
            logger.info("MySQL connection closed")

    def list_tables(self) -> list[str]:
        """List all tables in the database.

        Returns:
            List of table names.
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                f"WHERE TABLE_SCHEMA = '{self.database}' AND TABLE_TYPE = 'BASE TABLE'"
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
            cursor.execute(
                f"SELECT COLUMN_NAME, COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                f"WHERE TABLE_SCHEMA = '{self.database}' AND TABLE_NAME = '{table_name}'"
            )
            schema = {row[0]: row[1] for row in cursor.fetchall()}
            logger.debug(f"Schema for {table_name}: {len(schema)} columns")
            return schema
        finally:
            cursor.close()

    def get_row_count(self, table_name: str) -> int:
        """Get row count for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Approximate row count.
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
            limit: Maximum rows to return (MySQL LIMIT clause).

        Returns:
            List of result rows as dictionaries.
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor(dictionary=True)
        try:
            clean_sql = sql.strip().rstrip(";")
            # Add LIMIT if not already present
            if "LIMIT" not in clean_sql.upper():
                clean_sql = f"{clean_sql} LIMIT {limit}"

            cursor.execute(clean_sql)
            results = cursor.fetchall()
            logger.debug(f"Query returned {len(results)} rows")
            return results
        finally:
            cursor.close()


def create_mysql_connector(connection_uri: str) -> MySQLConnector:
    """Create a MySQL connector from a connection URI.

    Args:
        connection_uri: URI in format mysql://user:password@host:port/database

    Returns:
        MySQLConnector instance.

    Example:
        >>> conn = create_mysql_connector("mysql://root:password@localhost:3306/mydb")
    """
    from urllib.parse import urlparse

    parsed = urlparse(connection_uri)

    if parsed.scheme != "mysql":
        raise ValueError(f"Invalid scheme: {parsed.scheme}, expected 'mysql'")

    return MySQLConnector(
        host=parsed.hostname or "localhost",
        port=parsed.port or 3306,
        user=parsed.username or "root",
        password=parsed.password or "",
        database=parsed.path.lstrip("/") or "",
    )
