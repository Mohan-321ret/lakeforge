"""Oracle Database connector for Lakeforge."""

from typing import Any, Optional
import logging

from lakeforge.sources.registry import BaseConnector

logger = logging.getLogger(__name__)


class OracleConnector(BaseConnector):
    """Connector for Oracle Database."""

    def __init__(
        self,
        host: str,
        port: int = 1521,
        user: str = "system",
        password: str = "",
        database: str = "XE",
        sid: Optional[str] = None,
    ):
        """Initialize Oracle connector.

        Args:
            host: Oracle server hostname or IP
            port: Oracle port (default 1521)
            user: Database user
            password: Database password
            database: Database name (SID or service name)
            sid: Oracle SID (if different from database parameter)
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.sid = sid or database
        self.connection = None

    def connect(self) -> Any:
        """Establish connection to Oracle.

        Returns:
            Oracle connection object.

        Raises:
            ImportError: If oracledb not installed.
            Exception: If connection fails.
        """
        try:
            import oracledb
        except ImportError:
            raise ImportError(
                "oracledb not installed. "
                "Install with: pip install oracledb"
            )

        try:
            dsn = oracledb.makedsn(
                host=self.host,
                port=self.port,
                sid=self.sid,
            )
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=dsn,
            )
            logger.info(f"Connected to Oracle at {self.host}:{self.port}/{self.sid}")
            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to Oracle: {str(e)}")
            raise

    def close(self) -> None:
        """Close Oracle connection."""
        if self.connection:
            self.connection.close()
            logger.info("Oracle connection closed")

    def list_tables(self) -> list[str]:
        """List all tables owned by the user.

        Returns:
            List of table names.
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "SELECT TABLE_NAME FROM USER_TABLES ORDER BY TABLE_NAME"
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
                f"SELECT COLUMN_NAME, DATA_TYPE FROM USER_TAB_COLUMNS "
                f"WHERE TABLE_NAME = '{table_name.upper()}' ORDER BY COLUMN_ID"
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
            limit: Maximum rows to return.

        Returns:
            List of result rows as dictionaries.
        """
        if not self.connection:
            self.connect()

        clean_sql = sql.strip().rstrip(";")
        # Add ROWNUM restriction if not already present
        if "ROWNUM" not in clean_sql.upper():
            clean_sql = f"SELECT * FROM ({clean_sql}) WHERE ROWNUM <= {limit}"

        cursor = self.connection.cursor()
        try:
            cursor.execute(clean_sql)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            logger.debug(f"Query returned {len(results)} rows")
            return results
        finally:
            cursor.close()


def create_oracle_connector(connection_uri: str) -> OracleConnector:
    """Create an Oracle connector from a connection URI.

    Args:
        connection_uri: URI in format oracle://user:password@host:port/sid

    Returns:
        OracleConnector instance.

    Example:
        >>> conn = create_oracle_connector("oracle://system:password@localhost:1521/XE")
    """
    from urllib.parse import urlparse

    parsed = urlparse(connection_uri)

    if parsed.scheme != "oracle":
        raise ValueError(f"Invalid scheme: {parsed.scheme}, expected 'oracle'")

    return OracleConnector(
        host=parsed.hostname or "localhost",
        port=parsed.port or 1521,
        user=parsed.username or "system",
        password=parsed.password or "",
        database=parsed.path.lstrip("/") or "XE",
    )
