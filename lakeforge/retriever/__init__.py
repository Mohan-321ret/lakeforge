"""Retrieval module for searching catalog and data."""

from lakeforge.retriever.base import BaseRetriever
from lakeforge.retriever.dict_ import DictRetriever
from lakeforge.retriever.bm25 import BM25Retriever
from lakeforge.retriever.hybrid import HybridRetriever


def get_retriever(
    mode: str = "hybrid",
    use_dict: bool = True,
    use_bm25: bool = True,
) -> BaseRetriever:
    """
    Factory function to create a retriever.

    Args:
        mode: Retriever mode - "dict", "bm25", or "hybrid"
        use_dict: Enable DictRetriever (for hybrid mode)
        use_bm25: Enable BM25Retriever (for hybrid mode)

    Returns:
        Retriever instance

    Raises:
        ValueError: If mode is not recognized
    """
    if mode == "dict":
        return DictRetriever()
    elif mode == "bm25":
        return BM25Retriever()
    elif mode == "hybrid":
        return HybridRetriever(use_dict=use_dict, use_bm25=use_bm25)
    else:
        raise ValueError(f"Unknown retriever mode: {mode}")


__all__ = [
    "BaseRetriever",
    "DictRetriever",
    "BM25Retriever",
    "HybridRetriever",
    "get_retriever",
]
