"""Card models for search and retrieval."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class TableCard:
    """Card representing a table in the data source."""

    name: str
    """Table name."""
    row_count: Optional[int] = None
    """Number of rows in the table."""
    description: Optional[str] = None
    """User-provided description of the table."""
    columns_summary: List[str] = field(default_factory=list)
    """List of column names in the table."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "type": "table",
            "name": self.name,
            "row_count": self.row_count,
            "description": self.description,
            "columns_summary": self.columns_summary,
        }

    def render(self) -> str:
        """Render as text for indexing."""
        parts = [f"Table: {self.name}"]
        if self.row_count is not None:
            parts.append(f"Rows: {self.row_count}")
        if self.description:
            parts.append(f"Description: {self.description}")
        if self.columns_summary:
            parts.append(f"Columns: {', '.join(self.columns_summary)}")
        return "\n".join(parts)


@dataclass
class ColumnCard:
    """Card representing a column in a table."""

    table_name: str
    """Name of the parent table."""
    column_name: str
    """Name of the column."""
    data_type: str
    """Data type (e.g., VARCHAR, BIGINT, FLOAT)."""
    nullable: bool = True
    """Whether the column allows NULL values."""
    description: Optional[str] = None
    """User-provided description of the column."""
    sample_values: List[Any] = field(default_factory=list)
    """Sample values from the column."""
    statistics: Dict[str, Any] = field(default_factory=dict)
    """Column statistics (null_rate, unique_count, min, max, etc.)."""
    is_pii: bool = False
    """Whether the column contains PII."""
    pii_type: Optional[str] = None
    """Type of PII detected (email, phone, ssn, etc.)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "type": "column",
            "table_name": self.table_name,
            "column_name": self.column_name,
            "data_type": self.data_type,
            "nullable": self.nullable,
            "description": self.description,
            "sample_values": self.sample_values,
            "statistics": self.statistics,
            "is_pii": self.is_pii,
            "pii_type": self.pii_type,
        }

    def render(self) -> str:
        """Render as text for indexing."""
        parts = [f"Column: {self.table_name}.{self.column_name}"]
        parts.append(f"Type: {self.data_type}")
        if self.nullable:
            parts.append("Nullable: Yes")
        if self.description:
            parts.append(f"Description: {self.description}")
        if self.is_pii:
            pii_label = self.pii_type or "PII"
            parts.append(f"Contains: {pii_label}")
        if self.statistics:
            stats_str = ", ".join(
                f"{k}: {v}" for k, v in self.statistics.items() if v is not None
            )
            if stats_str:
                parts.append(f"Stats: {stats_str}")
        return "\n".join(parts)


@dataclass
class GlossaryCard:
    """Card representing a glossary term or business definition."""

    term: str
    """The term being defined."""
    definition: str
    """Definition of the term."""
    related_tables: List[str] = field(default_factory=list)
    """List of table names related to this term."""
    related_columns: List[str] = field(default_factory=list)
    """List of column identifiers (table.column) related to this term."""
    source: Optional[str] = None
    """Source of the definition (e.g., 'data_dictionary', 'user_provided')."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "type": "glossary",
            "term": self.term,
            "definition": self.definition,
            "related_tables": self.related_tables,
            "related_columns": self.related_columns,
            "source": self.source,
        }

    def render(self) -> str:
        """Render as text for indexing."""
        parts = [f"Glossary: {self.term}"]
        parts.append(f"Definition: {self.definition}")
        if self.related_tables:
            parts.append(f"Related Tables: {', '.join(self.related_tables)}")
        if self.related_columns:
            parts.append(f"Related Columns: {', '.join(self.related_columns)}")
        if self.source:
            parts.append(f"Source: {self.source}")
        return "\n".join(parts)


@dataclass
class RelationshipCard:
    """Card representing a relationship between tables."""

    source_table: str
    """Table that contains the foreign key."""
    source_column: str
    """Column that is the foreign key."""
    target_table: str
    """Table that is referenced."""
    target_column: str
    """Column that is the primary key."""
    relationship_type: str = "one_to_many"
    """Type of relationship (one_to_one, one_to_many, many_to_many)."""
    description: Optional[str] = None
    """Description of the relationship."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "type": "relationship",
            "source_table": self.source_table,
            "source_column": self.source_column,
            "target_table": self.target_table,
            "target_column": self.target_column,
            "relationship_type": self.relationship_type,
            "description": self.description,
        }

    def render(self) -> str:
        """Render as text for indexing."""
        parts = [
            f"Relationship: {self.source_table}.{self.source_column} -> {self.target_table}.{self.target_column}"
        ]
        parts.append(f"Type: {self.relationship_type}")
        if self.description:
            parts.append(f"Description: {self.description}")
        return "\n".join(parts)
