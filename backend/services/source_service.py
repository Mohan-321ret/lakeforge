"""Service layer for source management."""

import logging
from typing import List, Optional
from backend.models import SourceCreate, SourceResponse
from lakeforge.sources.registry import get_connector

logger = logging.getLogger(__name__)


class SourceService:
    """Service for managing data sources."""

    # Singleton in-memory store shared across all SourceService instances
    _sources: dict = {}
    _counter: int = 0

    def __init__(self):
        """Initialize source service."""
        pass

    @property
    def sources(self):
        return SourceService._sources

    @property
    def counter(self):
        return SourceService._counter

    @counter.setter
    def counter(self, value):
        SourceService._counter = value

    async def create_source(self, source: SourceCreate) -> SourceResponse:
        """Create a new data source.

        Args:
            source: Source creation data

        Returns:
            Created source response
        """
        # Validate URI format only (don't test connection - user can test later)
        # Connection test is optional via POST /{source_id}/test endpoint
        if not source.uri or "://" not in source.uri:
            raise ValueError(f"Invalid source URI format: {source.uri}")

        # Generate ID
        self.counter += 1
        source_id = f"src_{self.counter}"

        # Store in memory (in production: use database)
        response = SourceResponse(
            id=source_id,
            name=source.name,
            uri=source.uri,
            source_type=self._get_source_type(source.uri),
            description=source.description,
            tags=source.tags,
            created_at="2024-01-01T00:00:00Z",
            last_accessed=None,
            row_count=None,
            table_count=None,
        )
        self.sources[source_id] = response
        return response

    async def list_sources(self) -> List[SourceResponse]:
        """List all sources.

        Returns:
            List of sources
        """
        return list(self.sources.values())

    async def get_source(self, source_id: str) -> Optional[SourceResponse]:
        """Get a specific source.

        Args:
            source_id: ID of the source

        Returns:
            Source response or None
        """
        return self.sources.get(source_id)

    async def delete_source(self, source_id: str) -> bool:
        """Delete a source.

        Args:
            source_id: ID of the source

        Returns:
            True if deleted, False if not found
        """
        if source_id in self.sources:
            del self.sources[source_id]
            return True
        return False

    async def test_connection(self, source_id: str) -> dict:
        """Test a source connection.

        Args:
            source_id: ID of the source

        Returns:
            Test result
        """
        source = self.sources.get(source_id)
        if not source:
            return {"status": "error", "message": "Source not found"}

        try:
            connector = get_connector(source.uri)
            connector.connect()
            tables = connector.list_tables()
            connector.close()
            return {
                "status": "success",
                "message": f"Connected successfully, found {len(tables)} tables",
                "table_count": len(tables),
            }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def _get_source_type(uri: str) -> str:
        """Determine source type from URI.

        Args:
            uri: Connection URI

        Returns:
            Source type
        """
        if uri.startswith("postgres://"):
            return "postgres"
        elif uri.startswith("mysql://"):
            return "mysql"
        elif uri.startswith("mssql://") or uri.startswith("sqlserver://"):
            return "sqlserver"
        elif uri.startswith("oracle://"):
            return "oracle"
        elif uri.startswith("sqlite://"):
            return "sqlite"
        elif uri.startswith("databricks://"):
            return "databricks"
        elif uri.startswith("s3://"):
            return "s3"
        else:
            return "file"
