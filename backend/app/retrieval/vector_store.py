"""FAISS vector store for assessment retrieval."""

import json
import logging
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from app.catalog.models import Assessment
from app.retrieval.embeddings import embed_texts

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-backed vector store for semantic search over assessments."""

    def __init__(self, index: faiss.Index, assessments: list[Assessment]):
        self.index = index
        self.assessments = assessments  # Parallel array: index i → assessments[i]

    @property
    def size(self) -> int:
        return self.index.ntotal

    @classmethod
    def build(cls, assessments: list[Assessment]) -> "VectorStore":
        """Build a new FAISS index from a list of assessments."""
        if not assessments:
            # Create empty index with correct dimensionality
            index = faiss.IndexFlatIP(384)
            return cls(index, [])

        # Generate embedding texts
        texts = [a.embedding_text for a in assessments]
        logger.info("Embedding %d assessments...", len(texts))

        # Embed all texts
        embeddings = embed_texts(texts)

        # Build FAISS index (Inner Product on normalized vectors = cosine similarity)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        logger.info("Built FAISS index with %d vectors (dim=%d)", index.ntotal, dim)
        return cls(index, assessments)

    def save(self, directory: str) -> None:
        """Save index and metadata to disk."""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(path / "index.faiss"))

        # Save metadata (assessment IDs in order)
        metadata = [a.id for a in self.assessments]
        with open(path / "metadata.json", "w") as f:
            json.dump(metadata, f)

        logger.info("Saved FAISS index to %s", directory)

    @classmethod
    def load(cls, directory: str, catalog: list[Assessment]) -> "VectorStore":
        """Load a pre-built index from disk."""
        path = Path(directory)
        index_path = path / "index.faiss"
        metadata_path = path / "metadata.json"

        if not index_path.exists() or not metadata_path.exists():
            logger.warning("No pre-built index found at %s, building from catalog...", directory)
            store = cls.build(catalog)
            store.save(directory)
            return store

        # Load FAISS index
        index = faiss.read_index(str(index_path))

        # Load metadata and reconstruct ordered assessment list
        with open(metadata_path, "r") as f:
            assessment_ids = json.load(f)

        # Build lookup for fast matching
        catalog_map = {a.id: a for a in catalog}
        assessments = []
        for aid in assessment_ids:
            if aid in catalog_map:
                assessments.append(catalog_map[aid])
            else:
                logger.warning("Assessment ID %s in index but not in catalog", aid)

        logger.info("Loaded FAISS index with %d vectors", index.ntotal)
        return cls(index, assessments)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 15,
        filter_types: Optional[list[str]] = None,
        require_remote: Optional[bool] = None,
        max_duration: Optional[int] = None,
    ) -> list[tuple[Assessment, float]]:
        """
        Search the index and return ranked assessments with scores.
        Applies post-retrieval filters.
        """
        # Over-retrieve to account for filtering
        fetch_k = min(top_k * 3, self.size) if self.size > 0 else 0
        if fetch_k == 0:
            return []

        # FAISS search
        scores, indices = self.index.search(query_embedding, fetch_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.assessments):
                continue

            assessment = self.assessments[idx]

            # Apply filters
            if filter_types and not any(t in assessment.test_type for t in filter_types):
                continue
            if require_remote is True and not assessment.remote_support:
                continue
            if max_duration and assessment.duration and assessment.duration > max_duration:
                continue

            results.append((assessment, float(score)))

            if len(results) >= top_k:
                break

        return results
