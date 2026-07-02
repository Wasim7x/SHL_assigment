"""Pre-download the sentence-transformers model at build time.

Run during Docker build / Render build to avoid cold-start download.
Usage: python -m scripts.download_model
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

print(f"Downloading model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)
print(f"Model downloaded successfully (dim={model.get_embedding_dimension()})")
print(f"Model cached at: {model._model_card_text}")
