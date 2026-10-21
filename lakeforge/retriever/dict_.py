"""Dictionary-based retriever with exact match and substring search."""

import re
from typing import List, Dict, Tuple, Any, Optional
from collections import defaultdict

from lakeforge.retriever.base import BaseRetriever


class DictRetriever(BaseRetriever):
    """
    Simple dictionary-based retriever using exact-match and substring search.

    Supports:
    - Exact field matching (table name, column name)
    - Substring search in rendered text
    - Ranking by relevance (exact > partial > substring)
    """

    def __init__(self):
        """Initialize the retriever."""
        self.cards: Dict[str, Any] = {}
        """Mapping of card_id to card object."""
        self.rendered: Dict[str, str] = {}
        """Mapping of card_id to rendered text."""
        self._inverted_index: Dict[str, List[str]] = defaultdict(list)
        """Inverted index: term -> list of card_ids."""

    def index(self, cards: List[Any], rendered: Dict[str, str]) -> None:
        """
        Index cards for retrieval.

        Args:
            cards: List of Card objects
            rendered: Dict mapping card_id to rendered text
        """
        self.clear()

        # Store cards and rendered text
        for card_id, card in zip(rendered.keys(), cards):
            self.cards[card_id] = card
            self.rendered[card_id] = rendered[card_id]

        # Build inverted index from rendered text
        for card_id, text in rendered.items():
            # Extract terms (alphanumeric sequences, case-insensitive)
            terms = set(re.findall(r"\b\w+\b", text.lower()))
            for term in terms:
                self._inverted_index[term].append(card_id)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Any]]:
        """
        Search for relevant cards using exact/substring matching.

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of (card_id, score, card_object) tuples, ranked by relevance
        """
        if not query or not self.cards:
            return []

        query_lower = query.lower()
        query_terms = set(re.findall(r"\b\w+\b", query_lower))

        # Score each card
        scores: Dict[str, float] = {}

        for card_id, text in self.rendered.items():
            text_lower = text.lower()
            score = 0.0

            # 1. Exact string match (highest score)
            if query_lower in text_lower:
                score += 10.0

            # 2. Term frequency matching (medium score)
            for term in query_terms:
                # Count occurrences
                count = text_lower.count(term)
                if count > 0:
                    score += count * 2.0

            # 3. Partial word match (lower score)
            if query_lower in text_lower:
                score += 1.0

            if score > 0:
                scores[card_id] = score

        # Sort by score (descending) and return top_k
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]

        return [
            (card_id, score, self.cards[card_id])
            for card_id, score in sorted_results
        ]

    def search_by_table(self, table_name: str) -> List[Tuple[str, Any]]:
        """
        Search for all cards related to a specific table.

        Args:
            table_name: Name of the table to search

        Returns:
            List of (card_id, card_object) tuples
        """
        results = []

        for card_id, card in self.cards.items():
            card_dict = card.to_dict()
            card_type = card_dict.get("type")

            # Match table cards by name
            if card_type == "table" and card_dict.get("name") == table_name:
                results.append((card_id, card))

            # Match column cards by table name
            elif card_type == "column" and card_dict.get("table_name") == table_name:
                results.append((card_id, card))

        return results

    def search_by_column(
        self, table_name: str, column_name: str
    ) -> Optional[Tuple[str, Any]]:
        """
        Search for a specific column card.

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            (card_id, card_object) tuple or None if not found
        """
        for card_id, card in self.cards.items():
            card_dict = card.to_dict()
            if (
                card_dict.get("type") == "column"
                and card_dict.get("table_name") == table_name
                and card_dict.get("column_name") == column_name
            ):
                return (card_id, card)

        return None

    def search_pii_columns(self) -> List[Tuple[str, Any]]:
        """
        Search for all columns marked as containing PII.

        Returns:
            List of (card_id, card_object) tuples
        """
        results = []

        for card_id, card in self.cards.items():
            card_dict = card.to_dict()
            if card_dict.get("type") == "column" and card_dict.get("is_pii"):
                results.append((card_id, card))

        return results

    def get_card(self, card_id: str) -> Any:
        """
        Retrieve a specific card by ID.

        Args:
            card_id: Identifier of the card

        Returns:
            Card object

        Raises:
            KeyError: If card_id not found
        """
        return self.cards[card_id]

    def clear(self) -> None:
        """Clear all indexed cards."""
        self.cards.clear()
        self.rendered.clear()
        self._inverted_index.clear()
