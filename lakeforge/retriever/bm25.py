"""BM25-based retriever for semantic ranking."""

from typing import List, Tuple, Any
import re
from collections import Counter

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

from lakeforge.retriever.base import BaseRetriever


class BM25Retriever(BaseRetriever):
    """
    BM25-based retriever using TF-IDF scoring for relevance ranking.

    Uses Okapi BM25 algorithm for efficient, library-free semantic ranking
    without embeddings or LLM calls.
    """

    def __init__(self):
        """Initialize the BM25 retriever."""
        if BM25Okapi is None:
            raise ImportError(
                "rank-bm25 is required. Install with: pip install rank-bm25"
            )

        self.cards: dict[str, Any] = {}
        """Mapping of card_id to card object."""
        self.rendered: dict[str, str] = {}
        """Mapping of card_id to rendered text."""
        self.tokenized_corpus: List[List[str]] = []
        """Tokenized text for each card (for BM25)."""
        self.bm25: BM25Okapi | None = None
        """BM25 index (built during indexing)."""
        self.card_ids_ordered: List[str] = []
        """Card IDs in order of tokenized_corpus."""

    def index(self, cards: List[Any], rendered: dict[str, str]) -> None:
        """
        Index cards for BM25 retrieval.

        Args:
            cards: List of Card objects
            rendered: Dict mapping card_id to rendered text
        """
        self.cards.clear()
        self.rendered.clear()
        self.tokenized_corpus.clear()
        self.card_ids_ordered.clear()

        # Store cards and rendered text
        for card_id, card in zip(rendered.keys(), cards):
            self.cards[card_id] = card
            self.rendered[card_id] = rendered[card_id]

        # Tokenize all rendered text
        for card_id in rendered.keys():
            text = rendered[card_id]
            tokens = self._tokenize(text)
            self.tokenized_corpus.append(tokens)
            self.card_ids_ordered.append(card_id)

        # Build BM25 index
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Any]]:
        """
        Search for relevant cards using BM25 scoring.

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of (card_id, score, card_object) tuples, ranked by BM25 score
        """
        if not query or not self.bm25 or not self.cards:
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Build results with scores
        results = []
        for card_id, score in zip(self.card_ids_ordered, scores):
            if score > 0:
                results.append((card_id, float(score), self.cards[card_id]))

        # Sort by score descending and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25 indexing.

        Args:
            text: Input text

        Returns:
            List of tokens (lowercased, alphanumeric only)
        """
        # Lowercase
        text = text.lower()

        # Split on non-alphanumeric characters
        tokens = re.findall(r"\b\w+\b", text)

        # Remove common stopwords (optional, but improves results)
        stopwords = {
            "the", "a", "an", "and", "or", "but", "is", "are", "was",
            "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may",
            "might", "must", "can", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "if", "this", "that",
            "these", "those", "i", "you", "he", "she", "it", "we", "they",
        }

        tokens = [t for t in tokens if t not in stopwords and len(t) > 1]

        return tokens

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
        self.tokenized_corpus.clear()
        self.card_ids_ordered.clear()
        self.bm25 = None
