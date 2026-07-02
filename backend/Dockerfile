FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Pre-download the embedding model (avoids cold-start download)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Build FAISS index
RUN python -m scripts.build_index

# Expose port (Render uses $PORT env var)
EXPOSE 8000

# Start server - uses $PORT from environment, defaults to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
