"""DBeaver profile importer for Lakeforge.

IMPORTANT: DBeaver stores passwords encrypted in credentials-config.json.
We CANNOT extract plain-text passwords from DBeaver without its encryption keys.

The frontend's password prompt is intentional:
- DBeaver saves connection details but encrypts credentials for security
- Users must enter the password when importing to Lakeforge
- This is a best practice: credentials should not be auto-extracted from config files

Data sources are stored in data-sources.json:
- Connection metadata: host, port, database, driver
- These are NOT encrypted and can be extracted
- But passwords require user input during import

See: DBeaverProfileImporter.import_connection() which returns URI without password
The frontend (Settings.jsx) prompts for password and builds complete URI.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DBeaverProfileImporter:
    """Import database connections from DBeaver profiles."""

    # DBeaver stores connections in different locations per OS
    DBEAVER_PATHS = {
        "linux": Path.home() / ".dbeaver4/General/.dbeaver",
        "darwin": Path.home() / "Library/DBeaverData/workspace6/General/.dbeaver",
        "win32": Path.home() / "AppData/Roaming/DBeaverData/workspace6/General/.dbeaver",
    }

    @staticmethod
    def get_dbeaver_config_path() -> Optional[Path]:
        """Find DBeaver configuration directory.

        Returns:
            Path to DBeaver config or None if not found.
        """
        import sys

        platform = sys.platform
        if platform.startswith("linux"):
            path = DBeaverProfileImporter.DBEAVER_PATHS["linux"]
        elif platform == "darwin":
            path = DBeaverProfileImporter.DBEAVER_PATHS["darwin"]
        elif platform.startswith("win"):
            path = DBeaverProfileImporter.DBEAVER_PATHS["win32"]
        else:
            return None

        if path.exists():
            return path
        return None

    @staticmethod
    def list_connections() -> Dict[str, Dict[str, Any]]:
        """List all DBeaver saved connections.

        Returns:
            Dict mapping connection name to connection details.
        """
        config_path = DBeaverProfileImporter.get_dbeaver_config_path()
        if not config_path:
            logger.warning("DBeaver config not found")
            return {}

        # DBeaver stores connections in .dbeaver/data-sources.json
        connections_file = config_path / "data-sources.json"
        if not connections_file.exists():
            logger.warning(f"DBeaver connections file not found at {connections_file}")
            return {}

        try:
            with open(connections_file, "r") as f:
                config = json.load(f)

            connections = {}
            for conn_id, conn_data in config.get("connections", {}).items():
                connection_info = {
                    "name": conn_data.get("name", conn_id),
                    "driver": conn_data.get("provider", "unknown"),
                    "type": conn_data.get("type", ""),
                    "id": conn_id,
                }

                # Extract connection parameters
                connection_info["params"] = conn_data.get("configuration", {})
                connections[conn_id] = connection_info

            logger.info(f"Found {len(connections)} DBeaver connections")
            return connections
        except Exception as e:
            logger.error(f"Failed to read DBeaver config: {str(e)}")
            return {}

    @staticmethod
    def get_connection_uri(connection_name: str) -> Optional[str]:
        """Convert a DBeaver connection to a connection URI.

        Args:
            connection_name: Name or ID of the DBeaver connection.

        Returns:
            Connection URI for Lakeforge or None if not found.
        """
        connections = DBeaverProfileImporter.list_connections()
        if connection_name not in connections:
            return None

        conn = connections[connection_name]
        driver = conn.get("driver", "").lower()
        params = conn.get("params", {})
        
        # Log the raw parameters for debugging
        logger.info(f"Converting connection '{connection_name}' with driver '{driver}'")
        logger.info(f"Raw parameters: {params}")

        # Map DBeaver drivers to Lakeforge URI schemes
        if "postgres" in driver:
            uri = _build_postgres_uri(params)
        elif "mysql" in driver:
            uri = _build_mysql_uri(params)
        elif "sqlserver" in driver or "mssql" in driver:
            uri = _build_sqlserver_uri(params)
        elif "oracle" in driver:
            uri = _build_oracle_uri(params)
        elif "sqlite" in driver:
            uri = _build_sqlite_uri(params)
        else:
            logger.warning(f"Unsupported driver: {driver}")
            return None
        
        logger.info(f"Generated URI for {connection_name}: {uri[:30]}..." if uri else f"Failed to generate URI for {connection_name}")
        return uri

    @staticmethod
    def import_connection(
        dbeaver_connection_name: str, custom_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Import a DBeaver connection and return connection details.

        Args:
            dbeaver_connection_name: Name or ID of the DBeaver connection.
            custom_name: Custom name for this connection (optional).

        Returns:
            Dict with connection info and URI.

        Raises:
            ValueError: If connection not found or unsupported.
        """
        connections = DBeaverProfileImporter.list_connections()
        if dbeaver_connection_name not in connections:
            raise ValueError(f"Connection '{dbeaver_connection_name}' not found in DBeaver")

        conn = connections[dbeaver_connection_name]
        uri = DBeaverProfileImporter.get_connection_uri(dbeaver_connection_name)

        if not uri:
            raise ValueError(
                f"Could not convert DBeaver connection '{dbeaver_connection_name}' to URI"
            )

        params = conn.get("params", {})
        return {
            "name": custom_name or conn.get("name"),
            "driver": conn.get("driver"),
            "uri": uri,
            "host": params.get("host", ""),
            "database": params.get("database", ""),
            "dbeaver_id": dbeaver_connection_name,
        }




def _extract_password(params: Dict[str, Any]) -> str:
    """Extract password from DBeaver params with multiple fallback options.
    
    DBeaver stores passwords in various ways:
    - Direct: params['password']
    - Nested: params['properties']['password']
    - Alternative keys: pwd, passwd, secret, auth_password
    """
    logger.info(f"Extracting password - Available param keys: {list(params.keys())}")
    
    # Try direct password field (various names)
    password = (
        params.get("password") or
        params.get("pwd") or
        params.get("passwd") or
        params.get("secret") or
        params.get("auth_password") or
        params.get("authPassword") or
        ""
    )
    
    if password:
        logger.info(f"✅ Found password in direct params")
        return password
    
    # Try nested properties
    if isinstance(params.get("properties"), dict):
        props = params["properties"]
        logger.info(f"Found properties object - keys: {list(props.keys())}")
        password = (
            props.get("password") or
            props.get("pwd") or
            props.get("passwd") or
            props.get("secret") or
            props.get("auth_password") or
            props.get("authPassword") or
            ""
        )
        if password:
            logger.info(f"✅ Found password in properties object")
            return password
    
    # Try credentials object (some drivers use this)
    if isinstance(params.get("credentials"), dict):
        creds = params["credentials"]
        logger.info(f"Found credentials object - keys: {list(creds.keys())}")
        password = (
            creds.get("password") or
            creds.get("pwd") or
            creds.get("secret") or
            ""
        )
        if password:
            logger.info(f"✅ Found password in credentials object")
            return password
    
    logger.warning(f"❌ No password found in DBeaver connection params. Full param object: {params}")
    return ""


def _build_postgres_uri(params: Dict[str, Any]) -> str:
    """Build PostgreSQL URI from DBeaver params."""
    host = params.get("host") or params.get("server") or "localhost"
    port = params.get("port") or params.get("serverPort") or 5432
    user = params.get("user") or params.get("username") or "postgres"
    password = _extract_password(params)
    database = params.get("database") or params.get("databaseName") or ""

    # Handle nested properties
    if isinstance(params.get("properties"), dict):
        props = params["properties"]
        if not user or user == "postgres":
            user = props.get("user") or props.get("username") or user
        if not password:
            password = _extract_password(props)
        if not database:
            database = props.get("database") or props.get("databaseName") or database

    try:
        port = int(port)
    except (ValueError, TypeError):
        port = 5432

    creds = f"{user}"
    if password:
        creds += f":{password}"
    creds += "@"

    uri = f"postgres://{creds}{host}:{port}/{database}"
    logger.info(f"Built PostgreSQL URI - user: {user}, has_password: {bool(password)}, host: {host}")
    return uri


def _build_mysql_uri(params: Dict[str, Any]) -> str:
    """Build MySQL URI from DBeaver params."""
    host = params.get("host") or params.get("server") or "localhost"
    port = params.get("port") or params.get("serverPort") or 3306
    user = params.get("user") or params.get("username") or "root"
    password = _extract_password(params)
    database = params.get("database") or params.get("databaseName") or ""

    # Handle nested properties
    if isinstance(params.get("properties"), dict):
        props = params["properties"]
        if not user or user == "root":
            user = props.get("user") or props.get("username") or user
        if not password:
            password = _extract_password(props)
        if not database:
            database = props.get("database") or props.get("databaseName") or database

    try:
        port = int(port)
    except (ValueError, TypeError):
        port = 3306

    creds = f"{user}"
    if password:
        creds += f":{password}"
    creds += "@"

    uri = f"mysql://{creds}{host}:{port}/{database}"
    logger.info(f"Built MySQL URI - user: {user}, has_password: {bool(password)}, host: {host}")
    return uri


def _build_sqlserver_uri(params: Dict[str, Any]) -> str:
    """Build SQL Server URI from DBeaver params.
    
    DBeaver may store params in various formats:
    - Flat: {host, port, user, password, database}
    - Nested: {server, databaseName, properties: {user, password}}
    """
    # Try different key names that DBeaver might use
    host = (
        params.get("host") or 
        params.get("server") or 
        params.get("serverName") or 
        "localhost"
    )
    
    port = params.get("port") or params.get("serverPort") or 1433
    
    user = (
        params.get("user") or 
        params.get("username") or 
        params.get("userName") or 
        "sa"
    )
    
    password = _extract_password(params)
    
    database = (
        params.get("database") or 
        params.get("databaseName") or 
        "master"
    )
    
    # Handle nested properties object
    if isinstance(params.get("properties"), dict):
        props = params["properties"]
        if not user or user == "sa":
            user = props.get("user") or props.get("username") or user
        if not password:
            password = _extract_password(props)
        if database == "master":
            database = props.get("database") or props.get("databaseName") or database
    
    # Ensure port is int
    try:
        port = int(port)
    except (ValueError, TypeError):
        port = 1433
    
    # Build credentials
    creds = f"{user}"
    if password:
        creds += f":{password}"
    creds += "@"
    
    uri = f"mssql://{creds}{host}:{port}/{database}"
    logger.info(f"Built SQL Server URI - user: {user}, has_password: {bool(password)}, host: {host}, database: {database}")
    return uri


def _build_oracle_uri(params: Dict[str, Any]) -> str:
    """Build Oracle URI from DBeaver params."""
    host = params.get("host") or params.get("server") or "localhost"
    port = params.get("port") or params.get("serverPort") or 1521
    user = params.get("user") or params.get("username") or "system"
    password = _extract_password(params)
    sid = params.get("sid") or params.get("database") or params.get("databaseName") or "XE"

    # Handle nested properties
    if isinstance(params.get("properties"), dict):
        props = params["properties"]
        if not user or user == "system":
            user = props.get("user") or props.get("username") or user
        if not password:
            password = _extract_password(props)
        if sid == "XE":
            sid = props.get("sid") or props.get("database") or props.get("databaseName") or sid

    try:
        port = int(port)
    except (ValueError, TypeError):
        port = 1521

    creds = f"{user}"
    if password:
        creds += f":{password}"
    creds += "@"

    uri = f"oracle://{creds}{host}:{port}/{sid}"
    logger.info(f"Built Oracle URI - user: {user}, has_password: {bool(password)}, host: {host}, sid: {sid}")
    return uri


def _build_sqlite_uri(params: Dict[str, Any]) -> str:
    """Build SQLite URI from DBeaver params."""
    database_path = (
        params.get("database") or 
        params.get("databaseName") or 
        params.get("path") or 
        ""
    )
    
    # Handle nested properties
    if isinstance(params.get("properties"), dict):
        props = params["properties"]
        if not database_path:
            database_path = props.get("database") or props.get("databaseName") or props.get("path") or ""
    
    return f"sqlite:///{database_path}"
