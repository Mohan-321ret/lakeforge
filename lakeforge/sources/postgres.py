"""Postgres connector using SQLAlchemy and psycopg2."""

import os
from typing import Any
from urllib.parse import urlparse

from lakeforge.sources.registry import BaseConnector


class PostgresConnector(BaseConnector):
    """Connector for Postgres via SQLAlchemy."""

    def __init__(self, source: str):
        """Initialize Postgres connector.

        Args:
            source: Postgres URI (postgres://user:password@host:port/database/schema)
                   or connection string via POSTGRES_CONNECTION_STRING env var

        Raises:
            ImportError: If sqlalchemy or psycopg2 is not installed.
            ValueError: If connection fails.
        """
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.exc import OperationalError
        except ImportError:
            raise ImportError(
                "Postgres connector requires: pip install sqlalchemy psycopg2-binary"
            )

        self.source = source
        self.engine: Any = None
        self.connection: Any = None
        self.database: str = ""
        self.schema: str = ""

        self._connect()

    def _connect(self) -> None:
        """Establish connection to Postgres.

        Raises:
            ValueError: If connection fails.
        """
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import OperationalError

        # Parse URI or use connection string
        if self.source.startswith("postgres://"):
            parsed = urlparse(self.source)
            
            # Extract components
            user = parsed.username or "postgres"
            password = parsed.password or ""
            host = parsed.hostname or "localhost"
            port = parsed.port or 5432
            database = parsed.path.lstrip("/").split("/")[0]
            schema = parsed.path.lstrip("/").split("/")[1] if len(parsed.path.split("/")) > 2 else "public"

            # Build connection string
            if password:
                connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
            else:
                connection_string = f"postgresql+psycopg2://{user}@{host}:{port}/{database}"
        else:
            # Use environment variable or connection string parameter
            connection_string = os.getenv("POSTGRES_CONNECTION_STRING", self.source)
            database = "unknown"
            schema = "public"

        try:
            self.engine = create_engine(connection_string, echo=False)
            self.connection = self.engine.connect()
            self.database = database
            self.schema = schema
        except OperationalError as e:
            raise RuntimeError(f"Failed to connect to Postgres: {e}")

    def connect(self) -> Any:
        """Return Postgres connection."""
        if self.connection is None:
            self._connect()
        return self.connection

    def list_tables(self) -> list[str]:
        """List all tables in schema.

        Returns:
            List of table names.

        Raises:
            RuntimeError: If query fails.
        """
        if self.connection is None:
            raise RuntimeError("Not connected")

        try:
            from sqlalchemy import text

            query = text(
                f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{self.schema}' 
                AND table_type = 'BASE TABLE'
                """
            )
            result = self.connection.execute(query)
            return [row[0] for row in result]
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
            from sqlalchemy import text

            query = text(
                f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = '{self.schema}' 
                AND table_name = '{table_name}'
                ORDER BY ordinal_position
                """
            )
            result = self.connection.execute(query)
            schema = {row[0]: row[1] for row in result}
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
            from sqlalchemy import text

            query = text(f"SELECT COUNT(*) as count FROM {self.schema}.{table_name}")
            result = self.connection.execute(query)
            row = result.fetchone()
            return row[0] if row else 0
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
            from sqlalchemy import text

            # Add LIMIT if not present
            if "LIMIT" not in sql.upper():
                sql = f"{sql} LIMIT {limit}"

            query_obj = text(sql)
            result = self.connection.execute(query_obj)

            # Fetch column names
            column_names = list(result.keys())

            # Fetch results
            rows = result.fetchall()

            # Convert to list of dicts
            results = []
            for row in rows:
                results.append({column_names[i]: row[i] for i in range(len(column_names))})

            return results
        except Exception as e:
            raise RuntimeError(f"Query failed: {e}")

    def close(self) -> None:
        """Close connection to Postgres."""
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                pass
        if self.engine is not None:
            try:
                self.engine.dispose()
            except Exception:
                pass
        self.connection = None
        self.engine = None
