"""L1 Discovery: Extract structural metadata from sources."""

from typing import Any

from lakeforge.profile import (
    ColumnProfile,
    L2Profile,
    Sampler,
    TableProfile,
)
from lakeforge.sources import BaseConnector


class Catalog:
    """Normalized in-memory representation of a source's schema."""

    def __init__(self, source: str):
        """Initialize catalog.

        Args:
            source: Source URI.
        """
        self.source = source
        self.tables: dict[str, TableMetadata] = {}

    def add_table(self, table_metadata: "TableMetadata") -> None:
        """Add table metadata to catalog.

        Args:
            table_metadata: TableMetadata object.
        """
        self.tables[table_metadata.name] = table_metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert catalog to dictionary.

        Returns:
            Dict representation of catalog.
        """
        return {
            "source": self.source,
            "tables": {
                name: table.to_dict() for name, table in self.tables.items()
            },
        }


class TableMetadata:
    """Metadata for a single table."""

    def __init__(self, name: str, schema: dict[str, str], row_count: int):
        """Initialize table metadata.

        Args:
            name: Table name.
            schema: Dict mapping column name to type.
            row_count: Row count.
        """
        self.name = name
        self.schema = schema
        self.row_count = row_count
        self.columns: dict[str, ColumnMetadata] = {}

        # Create column metadata from schema
        for col_name, col_type in schema.items():
            self.columns[col_name] = ColumnMetadata(
                name=col_name,
                type=col_type,
                nullable=True,  # Phase 2 will add nullable detection
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict representation of table metadata.
        """
        return {
            "name": self.name,
            "row_count": self.row_count,
            "columns": {
                name: col.to_dict() for name, col in self.columns.items()
            },
        }


class ColumnMetadata:
    """Metadata for a single column."""

    def __init__(
        self,
        name: str,
        type: str,
        nullable: bool = True,
        ordinal_position: int = 0,
    ):
        """Initialize column metadata.

        Args:
            name: Column name.
            type: Column type (e.g., VARCHAR, INT64).
            nullable: Whether column allows nulls.
            ordinal_position: Position in table.
        """
        self.name = name
        self.type = type
        self.nullable = nullable
        self.ordinal_position = ordinal_position
        self.profile: dict[str, Any] = {}  # Phase 2 will populate

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict representation of column metadata.
        """
        return {
            "name": self.name,
            "type": self.type,
            "nullable": self.nullable,
            "ordinal_position": self.ordinal_position,
            "profile": self.profile,
        }


def discover_source(connector: BaseConnector, verbose: bool = False) -> Catalog:
    """Perform L1 discovery on a source (extract schema).

    Args:
        connector: Source connector.
        verbose: Enable verbose logging.

    Returns:
        Catalog object with table and column metadata.
    """
    catalog = Catalog(source=connector.source)

    # List tables
    tables = connector.list_tables()
    if verbose:
        print(f"Found {len(tables)} table(s)")

    for table_name in tables:
        if verbose:
            print(f"  Discovering: {table_name}")

        # Get schema
        schema = connector.get_schema(table_name)

        # Get row count
        row_count = connector.get_row_count(table_name)

        # Create table metadata
        table_meta = TableMetadata(
            name=table_name,
            schema=schema,
            row_count=row_count,
        )

        catalog.add_table(table_meta)

    return catalog


def profile_source(
    connector: BaseConnector,
    catalog: Catalog,
    verbose: bool = False,
    max_rows: int = 1000,
    masking_method: str = "hash",
) -> L2Profile:
    """Perform L2 profiling on a source (statistics + PII).

    Args:
        connector: Source connector.
        catalog: Catalog from L1 discovery.
        verbose: Enable verbose logging.
        max_rows: Max rows to sample per table.
        masking_method: PII masking method (hash or redact).

    Returns:
        L2Profile object with statistics and PII detection.
    """
    profile = L2Profile(source=connector.source, masking_method=masking_method)
    sampler = Sampler(max_rows=max_rows)

    for table_name, table_meta in catalog.tables.items():
        if verbose:
            print(f"  Profiling: {table_name}")

        # Sample rows
        sample_rows = sampler.sample_from_connector(connector, table_name)
        sample_count = len(sample_rows)

        # Create table profile
        table_profile = TableProfile(
            name=table_name,
            row_count=table_meta.row_count,
            sample_count=sample_count,
        )

        # Profile each column
        for col_name, col_type in table_meta.schema.items():
            # Extract sample values for this column
            sample_values = [row.get(col_name) for row in sample_rows]

            # Create column profile
            col_profile = ColumnProfile(
                name=col_name,
                type=col_type,
                nullable=table_meta.columns[col_name].nullable,
                sample_values=sample_values,
            )

            table_profile.add_column_profile(col_profile)

        profile.add_table_profile(table_profile)

    return profile
