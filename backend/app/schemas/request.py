"""Request schemas for the chat API."""

from pydantic import BaseModel, field_validator
from typing import Literal


class Message(BaseModel):
    """A single message in the conversation."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    messages: list[Message]

    @field_validator("messages")
    @classmethod
    def enforce_non_empty(cls, v: list[Message]) -> list[Message]:
        if not v:
            raise ValueError("messages must contain at least one message")
        return v

    @field_validator("messages")
    @classmethod
    def last_message_is_user(cls, v: list[Message]) -> list[Message]:
        if v and v[-1].role != "user":
            raise ValueError("Last message must be from user")
        return v
