"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.catalog.loader import load_catalog
from app.retrieval.vector_store import VectorStore
from app.routes.health import router as health_router
from app.routes.chat import router as chat_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load catalog and FAISS index on startup."""
    # Resolve paths relative to the app directory
    base_dir = Path(__file__).parent.parent
    catalog_path = base_dir / settings.CATALOG_PATH
    index_path = base_dir / settings.FAISS_INDEX_PATH

    logger.info("Loading catalog from %s", catalog_path)
    app.state.catalog = load_catalog(str(catalog_path))
    logger.info("Loaded %d assessments", len(app.state.catalog))

    logger.info("Loading FAISS index from %s", index_path)
    app.state.vector_store = VectorStore.load(
        str(index_path), app.state.catalog
    )
    logger.info("FAISS index ready with %d vectors", app.state.vector_store.size)

    yield

    # Cleanup LLM client on shutdown
    from app.llm.gemini import get_llm_client
    try:
        client = get_llm_client()
        await client.close()
    except Exception:
        pass
    logger.info("Shutting down")


app = FastAPI(
    title="SHL Assessment Recommender",
    description="Conversational agent for SHL assessment selection",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
