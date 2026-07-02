"""High-level retrieval interface combining embedding + vector search."""

import logging
from typing import Optional

from app.catalog.models import Assessment
from app.retrieval.embeddings import embed_query
from app.retrieval.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieves relevant assessments given a natural language query."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 15,
        filter_types: Optional[list[str]] = None,
        require_remote: Optional[bool] = None,
        max_duration: Optional[int] = None,
    ) -> list[tuple[Assessment, float]]:
        """
        Embed the query and search the vector store.

        Args:
            query: Natural language search query built from conversation context
            top_k: Maximum number of results to return
            filter_types: Only return assessments matching these type codes
            require_remote: If True, only return remotely-administrable tests
            max_duration: Maximum test duration in minutes

        Returns:
            List of (Assessment, score) tuples, ranked by relevance
        """
        if not query.strip():
            return []

        # Embed the query
        query_vector = embed_query(query)

        # Search with filters
        results = self.vector_store.search(
            query_embedding=query_vector,
            top_k=top_k,
            filter_types=filter_types,
            require_remote=require_remote,
            max_duration=max_duration,
        )

        logger.info(
            "Retrieved %d results for query: '%s' (filters: types=%s, remote=%s, dur<=%s)",
            len(results),
            query[:80],
            filter_types,
            require_remote,
            max_duration,
        )

        return results
