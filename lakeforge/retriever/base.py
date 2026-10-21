"""Base retriever interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any


class BaseRetriever(ABC):
    """Abstract base class for retrieval systems."""

    @abstractmethod
    def index(self, cards: List[Any], rendered: Dict[str, str]) -> None:
        """
        Index cards for retrieval.

        Args:
            cards: List of Card objects
            rendered: Dict mapping card_id to rendered text
        """
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Any]]:
        """
        Search for relevant cards.

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of (card_id, score, card_object) tuples, ranked by relevance
        """
        pass

    @abstractmethod
    def get_card(self, card_id: str) -> Any:
        """
        Retrieve a specific card by ID.

        Args:
            card_id: Identifier of the card

        Returns:
            Card object
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all indexed cards."""
        pass
