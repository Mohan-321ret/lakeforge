"""Hybrid retriever router for selecting between exact match and semantic search."""

import re
from typing import List, Tuple, Any

from lakeforge.retriever.base import BaseRetriever
from lakeforge.retriever.dict_ import DictRetriever
from lakeforge.retriever.bm25 import BM25Retriever


class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever that routes queries to the most appropriate strategy.

    Strategy selection:
    - Exact/simple queries (table/column names) → DictRetriever
    - Complex/semantic queries (descriptions) → BM25Retriever
    - Combination of both for best results
    """

    def __init__(self, use_dict: bool = True, use_bm25: bool = True):
        """
        Initialize hybrid retriever.

        Args:
            use_dict: Enable DictRetriever (default: True)
            use_bm25: Enable BM25Retriever (default: True)
        """
        self.use_dict = use_dict
        self.use_bm25 = use_bm25

        self.dict_retriever = DictRetriever() if use_dict else None
        self.bm25_retriever = BM25Retriever() if use_bm25 else None

    def index(self, cards: List[Any], rendered: dict[str, str]) -> None:
        """
        Index cards for both retrieval strategies.

        Args:
            cards: List of Card objects
            rendered: Dict mapping card_id to rendered text
        """
        if self.dict_retriever:
            self.dict_retriever.index(cards, rendered)

        if self.bm25_retriever:
            self.bm25_retriever.index(cards, rendered)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Any]]:
        """
        Search using hybrid strategy.

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of (card_id, score, card_object) tuples, ranked by combined score
        """
        if not query:
            return []

        # Decide search strategy
        strategy = self._select_strategy(query)

        if strategy == "exact":
            return self._search_exact(query, top_k)
        elif strategy == "semantic":
            return self._search_semantic(query, top_k)
        else:  # hybrid
            return self._search_hybrid(query, top_k)

    def _select_strategy(self, query: str) -> str:
        """
        Select retrieval strategy based on query characteristics.

        Args:
            query: Search query

        Returns:
            One of: "exact", "semantic", "hybrid"
        """
        query_lower = query.lower()

        # Check if it's likely an exact match query
        # - Very short (1-3 words)
        # - No description keywords (describe, definition, meaning, etc.)
        # - Contains table/column separators (.)
        words = query.split()
        has_separators = "." in query
        has_semantic_keywords = any(
            kw in query_lower
            for kw in [
                "describe",
                "definition",
                "meaning",
                "what",
                "explain",
                "find",
                "show",
            ]
        )

        if len(words) <= 2 and not has_semantic_keywords:
            return "exact"
        elif has_semantic_keywords or len(words) > 3:
            return "semantic"
        else:
            return "hybrid"

    def _search_exact(self, query: str, top_k: int) -> List[Tuple[str, float, Any]]:
        """Search using exact match only."""
        if self.dict_retriever:
            return self.dict_retriever.search(query, top_k)
        return []

    def _search_semantic(
        self, query: str, top_k: int
    ) -> List[Tuple[str, float, Any]]:
        """Search using semantic ranking only."""
        if self.bm25_retriever:
            return self.bm25_retriever.search(query, top_k)
        return []

    def _search_hybrid(self, query: str, top_k: int) -> List[Tuple[str, float, Any]]:
        """Search using both methods and combine results."""
        results_dict = {}
        results_bm25 = {}

        # Get results from both retrievers
        if self.dict_retriever:
            dict_results = self.dict_retriever.search(query, top_k * 2)
            for card_id, score, card in dict_results:
                # Normalize dict scores to 0-10 range
                normalized_score = min(score, 10.0)
                results_dict[card_id] = (normalized_score, card)

        if self.bm25_retriever:
            bm25_results = self.bm25_retriever.search(query, top_k * 2)
            for card_id, score, card in bm25_results:
                # BM25 scores are typically 0-30+, normalize
                normalized_score = min(score / 3.0, 10.0)
                results_bm25[card_id] = (normalized_score, card)

        # Merge results with weighted average
        combined = {}
        all_cards = set(results_dict.keys()) | set(results_bm25.keys())

        for card_id in all_cards:
            dict_score = results_dict.get(card_id, (0.0, None))[0]
            bm25_score = results_bm25.get(card_id, (0.0, None))[0]

            # Weighted average: 40% dict, 60% BM25 for semantic queries
            combined_score = 0.4 * dict_score + 0.6 * bm25_score

            # Get card from either retriever
            card = results_dict.get(card_id, (0.0, None))[1]
            if card is None:
                card = results_bm25.get(card_id, (0.0, None))[1]

            combined[card_id] = (combined_score, card)

        # Sort by score and return top_k
        sorted_results = sorted(
            combined.items(), key=lambda x: x[1][0], reverse=True
        )[:top_k]

        return [(card_id, score, card) for card_id, (score, card) in sorted_results]

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
        if self.dict_retriever:
            try:
                return self.dict_retriever.get_card(card_id)
            except KeyError:
                pass

        if self.bm25_retriever:
            try:
                return self.bm25_retriever.get_card(card_id)
            except KeyError:
                pass

        raise KeyError(f"Card not found: {card_id}")

    def clear(self) -> None:
        """Clear all indexed cards."""
        if self.dict_retriever:
            self.dict_retriever.clear()

        if self.bm25_retriever:
            self.bm25_retriever.clear()
