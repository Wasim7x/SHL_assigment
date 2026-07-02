#!/usr/bin/env bash
# Build script for Render deployment (native Python runtime)
# This runs during the build phase on Render

set -e

echo "=== Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Pre-downloading embedding model ==="
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

echo "=== Building FAISS index ==="
python -m scripts.build_index

echo "=== Build complete ==="
