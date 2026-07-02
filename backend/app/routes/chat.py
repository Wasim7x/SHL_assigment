"""Chat endpoint — main conversational interface."""

import asyncio
import logging

from fastapi import APIRouter, Request, HTTPException

from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse
from app.agent.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    """
    Stateless chat endpoint. Takes full conversation history,
    returns next agent reply + optional recommendations.
    """
    orchestrator = Orchestrator(
        catalog=request.app.state.catalog,
        vector_store=request.app.state.vector_store,
    )

    try:
        result = await asyncio.wait_for(
            orchestrator.run(body.messages),
            timeout=28.0,  # 2s buffer under the 30s evaluator limit
        )
        return result
    except asyncio.TimeoutError:
        logger.error("Chat request timed out after 28s")
        raise HTTPException(
            status_code=504,
            detail="Request processing timed out",
        )
    except Exception as e:
        logger.exception(f"Error processing chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        )
