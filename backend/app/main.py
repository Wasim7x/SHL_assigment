"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

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
    logger.info("Loading catalog from %s", settings.CATALOG_PATH)
    app.state.catalog = load_catalog(settings.CATALOG_PATH)
    logger.info("Loaded %d assessments", len(app.state.catalog))

    logger.info("Loading FAISS index from %s", settings.FAISS_INDEX_PATH)
    app.state.vector_store = VectorStore.load(
        settings.FAISS_INDEX_PATH, app.state.catalog
    )
    logger.info("FAISS index ready with %d vectors", app.state.vector_store.size)

    yield

    logger.info("Shutting down")


app = FastAPI(
    title="SHL Assessment Recommender",
    description="Conversational agent for SHL assessment selection",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend from any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
