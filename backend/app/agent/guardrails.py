"""Guardrails: scope validation, injection detection, recommendation validation."""

import re
import logging
from dataclasses import dataclass
from typing import Optional

from app.schemas.request import Message
from app.catalog.models import Assessment

logger = logging.getLogger(__name__)

# Off-topic keywords that indicate a clearly out-of-scope request
OFF_TOPIC_PATTERNS = [
    r"\b(legal|lawsuit|sue|attorney|lawyer)\b",
    r"\b(medical|diagnosis|treatment|prescription)\b",
    r"\b(salary|compensation|pay range|benefits)\b",
    r"\b(stock|crypto|bitcoin|invest)\b",
    r"\b(recipe|cook|food)\b",
    r"\b(weather|sports score)\b",
    r"\b(write me a|generate code|build an app)\b",
]

# Prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore\b.*\binstructions",
    r"forget\b.*\binstructions",
    r"disregard\b.*\b(instructions|rules|guidelines)",
    r"you are now",
    r"new role:",
    r"system prompt:",
    r"pretend you are",
    r"act as if",
    r"override\b.*\brules",
    r"do not follow",
]


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""

    is_blocked: bool
    reason: Optional[str] = None
    message: Optional[str] = None


def count_turns(messages: list[Message]) -> int:
    """Count the number of conversation turns (user+assistant pairs)."""
    return (len(messages) + 1) // 2


def check_scope(messages: list[Message]) -> GuardrailResult:
    """
    Run hard-coded guardrail checks BEFORE any LLM call.

    Returns a GuardrailResult indicating whether the request should be blocked.
    """
    if not messages:
        return GuardrailResult(is_blocked=True, reason="empty", message="No messages provided.")

    latest = messages[-1].content.lower()

    # 1. Turn limit enforcement
    turns = count_turns(messages)
    if turns > 8:
        return GuardrailResult(
            is_blocked=True,
            reason="turn_limit",
            message="We've reached the conversation limit. Please start a new conversation if you need further help.",
        )

    # 2. Prompt injection detection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, latest, re.IGNORECASE):
            logger.warning("Injection attempt detected: %s", latest[:100])
            return GuardrailResult(
                is_blocked=True,
                reason="injection",
                message="I can only help with SHL assessment recommendations. How can I assist you in finding the right assessment?",
            )

    # 3. Obviously off-topic (only if clearly not assessment-related)
    # Check if message has ANY assessment-related keywords first
    assessment_keywords = [
        "assess", "test", "hire", "hiring", "candidate", "recruit",
        "skill", "evaluation", "shl", "personality", "cognitive",
        "developer", "engineer", "manager", "role", "job", "position",
        "recommend", "compare", "opq", "verify", "competency",
    ]
    has_assessment_context = any(kw in latest for kw in assessment_keywords)

    if not has_assessment_context:
        for pattern in OFF_TOPIC_PATTERNS:
            if re.search(pattern, latest, re.IGNORECASE):
                return GuardrailResult(
                    is_blocked=True,
                    reason="off_topic",
                    message="I specialize in SHL assessment recommendations only. I can help you find the right assessments for hiring, development, or evaluation needs. What role or skill area would you like to assess?",
                )

    return GuardrailResult(is_blocked=False)


def validate_recommendations(
    recommendations: list[dict],
    catalog: list[Assessment],
) -> list[dict]:
    """
    Post-generation validation: ensure every recommendation URL exists in catalog.
    This is the critical safety net against hallucinated URLs.
    """
    valid_urls = {a.url for a in catalog}
    valid_names = {a.name.lower(): a for a in catalog}

    validated = []
    for rec in recommendations:
        url = rec.get("url", "")
        name = rec.get("name", "")

        # Check URL validity
        if url in valid_urls:
            validated.append(rec)
        elif name.lower() in valid_names:
            # Fix URL from catalog if name matches
            correct_assessment = valid_names[name.lower()]
            rec["url"] = correct_assessment.url
            validated.append(rec)
        else:
            logger.warning(
                "Filtered out hallucinated recommendation: name='%s' url='%s'",
                name,
                url,
            )

    return validated
