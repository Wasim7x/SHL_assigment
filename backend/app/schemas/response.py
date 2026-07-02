"""Response schemas for the chat API."""

from pydantic import BaseModel


class Recommendation(BaseModel):
    """A single assessment recommendation."""

    name: str
    url: str
    test_type: str  # A, B, C, D, E, K, P, S


class ChatResponse(BaseModel):
    """Response body for POST /chat."""

    reply: str
    recommendations: list[Recommendation]  # Empty when clarifying/refusing
    end_of_conversation: bool
