"""Sentence-Transformer embedding wrapper."""

import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load and cache the embedding model (singleton)."""
    logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    logger.info("Embedding model loaded (dim=%d)", model.get_embedding_dimension())
    return model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts into normalized vectors."""
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.array(embeddings, dtype=np.float32)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string into a normalized vector."""
    model = get_embedding_model()
    embedding = model.encode([query], normalize_embeddings=True, show_progress_bar=False)
    return np.array(embedding, dtype=np.float32)
