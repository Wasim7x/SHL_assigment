"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Readiness probe — returns 200 with status ok."""
    return {"status": "ok"}
