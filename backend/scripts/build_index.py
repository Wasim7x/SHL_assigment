"""Build FAISS index from catalog.json.

Run this script to generate the pre-built FAISS index:
    cd backend && python -m scripts.build_index
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.catalog.loader import load_catalog
from app.retrieval.vector_store import VectorStore
from app.config import settings


def main():
    print(f"Loading catalog from {settings.CATALOG_PATH}...")
    catalog = load_catalog(settings.CATALOG_PATH)
    print(f"Loaded {len(catalog)} assessments")

    print("Building FAISS index (this may take a moment on first run)...")
    vector_store = VectorStore.build(catalog)
    print(f"Built index with {vector_store.size} vectors")

    print(f"Saving index to {settings.FAISS_INDEX_PATH}...")
    vector_store.save(settings.FAISS_INDEX_PATH)
    print("Done! Index saved successfully.")


if __name__ == "__main__":
    main()
