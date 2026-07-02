"""Tests for schema validation."""

import pytest
from pydantic import ValidationError
from app.schemas.request import ChatRequest, Message
from app.schemas.response import ChatResponse, Recommendation


class TestChatRequest:
    def test_valid_request(self):
        req = ChatRequest(messages=[
            Message(role="user", content="Hello")
        ])
        assert len(req.messages) == 1

    def test_empty_messages_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(messages=[])

    def test_last_message_must_be_user(self):
        with pytest.raises(ValidationError):
            ChatRequest(messages=[
                Message(role="user", content="Hi"),
                Message(role="assistant", content="Hello"),
            ])

    def test_multi_turn_valid(self):
        req = ChatRequest(messages=[
            Message(role="user", content="Hi"),
            Message(role="assistant", content="Hello"),
            Message(role="user", content="Help me"),
        ])
        assert len(req.messages) == 3


class TestChatResponse:
    def test_response_with_recommendations(self):
        resp = ChatResponse(
            reply="Here are my recommendations",
            recommendations=[
                Recommendation(name="Java 8", url="https://shl.com/test", test_type="K"),
            ],
            end_of_conversation=True,
        )
        assert len(resp.recommendations) == 1
        assert resp.end_of_conversation is True

    def test_response_without_recommendations(self):
        resp = ChatResponse(
            reply="Can you tell me more?",
            recommendations=[],
            end_of_conversation=False,
        )
        assert len(resp.recommendations) == 0

    def test_response_schema_serialization(self):
        resp = ChatResponse(
            reply="Test",
            recommendations=[
                Recommendation(name="OPQ32r", url="https://shl.com/opq", test_type="P"),
            ],
            end_of_conversation=False,
        )
        data = resp.model_dump()
        assert "reply" in data
        assert "recommendations" in data
        assert "end_of_conversation" in data
        assert data["recommendations"][0]["test_type"] == "P"
