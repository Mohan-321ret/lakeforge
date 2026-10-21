"""Base classes for document ingestion."""

from abc import ABC, abstractmethod
from typing import List, Any
from pathlib import Path


class BaseDocIngester(ABC):
    """Abstract base class for document ingesters."""

    @abstractmethod
    def ingest(self, source: str | Path) -> List[Any]:
        """
        Ingest documents and return list of Card objects.

        Args:
            source: Path to document file or directory

        Returns:
            List of Card objects (TableCard, ColumnCard, GlossaryCard, etc.)
        """
        pass

    @abstractmethod
    def supports(self, source: str | Path) -> bool:
        """
        Check if this ingester can handle the given source.

        Args:
            source: Path to document

        Returns:
            True if this ingester can handle the source
        """
        pass
