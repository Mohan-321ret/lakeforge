"""Microsoft SQL Server connector for Lakeforge."""

from typing import Any, Optional
import logging

from lakeforge.sources.registry import BaseConnector

logger = logging.getLogger(__name__)


class SQLServerConnector(BaseConnector):
    """Connector for Microsoft SQL Server databases."""

    def __init__(
        self,
        server: str,
        port: int = 1433,
        user: str = "sa",
        password: str = "",
        database: str = "master",
        driver: str = "ODBC Driver 17 for SQL Server",
    ):
        """Initialize SQL Server connector.

        Args:
            server: SQL Server hostname or IP
            port: SQL Server port (default 1433)
            user: Database user
            password: Database password
            database: Default database name
            driver: ODBC driver name
        """
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.driver = driver
        self.connection = None

    def connect(self) -> Any:
        """Establish connection to SQL Server.

        Tries pymssql first (no ODBC driver needed), falls back to pyodbc.

        Returns:
            SQL Server connection object.

        Raises:
            ImportError: If neither pymssql nor pyodbc available.
            Exception: If connection fails.
        """
        # Try pymssql first (no ODBC driver required)
        try:
            import pymssql
            try:
                self.connection = pymssql.connect(
                    server=self.server,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    timeout=10
                )
                logger.info(f"✅ Connected to SQL Server (pymssql) at {self.server}:{self.port}/{self.database}")
                return self.connection
            except Exception as e:
                logger.warning(f"pymssql connection failed: {str(e)}")
                # Fall through to try pyodbc
        except ImportError:
            logger.debug("pymssql not available, trying pyodbc...")

        # Try pyodbc as fallback
        try:
            import pyodbc
            try:
                connection_string = (
                    f"Driver={{{self.driver}}};Server={self.server},{self.port};"
                    f"Database={self.database};UID={self.user};PWD={self.password};"
                )
                self.connection = pyodbc.connect(connection_string)
                logger.info(f"✅ Connected to SQL Server (pyodbc) at {self.server}:{self.port}/{self.database}")
                return self.connection
            except Exception as e:
                logger.error(f"pyodbc connection failed: {str(e)}")
                raise
        except ImportError:
            pass

        # No connection method available
        raise ImportError(
            "SQL Server connection requires either pymssql or pyodbc.\n\n"
            "Install pymssql (recommended, no ODBC driver needed):\n"
            "  pip install pymssql\n\n"
            "Or install pyodbc (requires ODBC driver):\n"
            "  pip install pyodbc"
        )

    def close(self) -> None:
        """Close SQL Server connection."""
        if self.connection:
            self.connection.close()
            logger.info("SQL Server connection closed")

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
                f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                f"WHERE TABLE_CATALOG = '{self.database}' AND TABLE_TYPE = 'BASE TABLE'"
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
                f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                f"WHERE TABLE_CATALOG = '{self.database}' AND TABLE_NAME = '{table_name}'"
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
            cursor.execute(
                f"SELECT COUNT(*) FROM [{self.database}].dbo.[{table_name}]"
            )
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

        # Add TOP clause if not already present
        if "TOP" not in sql.upper():
            sql = sql.replace("SELECT", f"SELECT TOP {limit}", 1)

        cursor = self.connection.cursor()
        try:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            logger.debug(f"Query returned {len(results)} rows")
            return results
        finally:
            cursor.close()


def create_sqlserver_connector(connection_uri: str) -> SQLServerConnector:
    """Create a SQL Server connector from a connection URI.

    Args:
        connection_uri: URI in format mssql://user:password@server:port/database

    Returns:
        SQLServerConnector instance.

    Example:
        >>> conn = create_sqlserver_connector("mssql://sa:password@localhost:1433/mydb")
    """
    from urllib.parse import urlparse

    parsed = urlparse(connection_uri)

    if parsed.scheme not in ("mssql", "sqlserver"):
        raise ValueError(f"Invalid scheme: {parsed.scheme}, expected 'mssql' or 'sqlserver'")

    return SQLServerConnector(
        server=parsed.hostname or "localhost",
        port=parsed.port or 1433,
        user=parsed.username or "sa",
        password=parsed.password or "",
        database=parsed.path.lstrip("/") or "master",
    )
