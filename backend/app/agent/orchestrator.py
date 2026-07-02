"""Agent orchestrator — the central decision engine.

Routes each request through: guardrails → intent classification → behavior dispatch.
"""

import re
import logging
from enum import Enum

from app.schemas.request import Message
from app.schemas.response import ChatResponse
from app.catalog.models import Assessment
from app.retrieval.vector_store import VectorStore
from app.retrieval.retriever import Retriever
from app.llm.gemini import get_llm_client
from app.agent.guardrails import check_scope, count_turns
from app.agent.prompts import SYSTEM_PROMPT, INTENT_CLASSIFICATION_PROMPT
from app.agent.behaviors import (
    handle_clarify,
    handle_recommend,
    handle_refine,
    handle_compare,
    handle_refuse,
    format_conversation,
)

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    CLARIFY = "CLARIFY"
    RECOMMEND = "RECOMMEND"
    REFINE = "REFINE"
    COMPARE = "COMPARE"
    REFUSE = "REFUSE"


class Orchestrator:
    """
    Main agent orchestrator. For each request:
    1. Run guardrail checks (hard-coded, no LLM)
    2. Classify intent (hard rules + LLM fallback)
    3. Dispatch to the appropriate behavior handler
    """

    def __init__(self, catalog: list[Assessment], vector_store: VectorStore):
        self.catalog = catalog
        self.vector_store = vector_store
        self.retriever = Retriever(vector_store)

    async def run(self, messages: list[Message]) -> ChatResponse:
        """Process a conversation and return the next response."""

        # Phase 1: Guardrails (hard-coded, fast)
        guardrail_result = check_scope(messages)
        if guardrail_result.is_blocked:
            logger.info("Request blocked by guardrails: %s", guardrail_result.reason)
            return ChatResponse(
                reply=guardrail_result.message or "I can only help with SHL assessment recommendations.",
                recommendations=[],
                end_of_conversation=guardrail_result.reason == "turn_limit",
            )

        # Phase 2: Classify intent
        intent = await self._classify_intent(messages)
        logger.info("Classified intent: %s", intent)

        # Phase 3: Dispatch to behavior handler
        return await self._dispatch(intent, messages)

    async def _classify_intent(self, messages: list[Message]) -> Intent:
        """
        Classify the user's intent using hard-coded rules first,
        falling back to Gemini for ambiguous cases.
        """
        latest = messages[-1].content.lower()
        turns = count_turns(messages)

        # Rule 1: Force RECOMMEND at turn 7+ (approaching 8-turn limit)
        if turns >= 7:
            logger.info("Turn %d: forcing RECOMMEND (approaching limit)", turns)
            return Intent.RECOMMEND

        # Rule 2: Detect COMPARE pattern
        compare_patterns = [
            r"(compare|difference|differ|vs\.?|versus)\s",
            r"(what.s the difference|how .+ differ|which is better)",
            r"(between .+ and .+)",
        ]
        if any(re.search(p, latest, re.IGNORECASE) for p in compare_patterns):
            return Intent.COMPARE

        # Rule 3: Detect REFINE (previous response had recommendations + user adds constraint)
        has_previous_recs = self._has_previous_recommendations(messages)
        if has_previous_recs:
            refine_signals = [
                r"(also|add|include|additionally)",
                r"(remove|exclude|drop|without)",
                r"(actually|instead|but|shorter|longer|faster)",
                r"(what about|how about|can you also)",
                r"(personality|cognitive|knowledge|skill|behavior)",
            ]
            if any(re.search(p, latest, re.IGNORECASE) for p in refine_signals):
                return Intent.REFINE

        # Rule 4: Turn 1 + very vague (too short and no role/job)
        if turns == 1 and len(latest.split()) < 8:
            role_indicators = [
                "developer", "engineer", "manager", "analyst", "designer",
                "sales", "marketing", "finance", "accountant", "nurse",
                "teacher", "executive", "director", "supervisor", "admin",
                "customer service", "support", "hiring", "recruit",
            ]
            has_role = any(r in latest for r in role_indicators)

            # Check for job description indicator
            has_jd = "job description" in latest or "jd" in latest or len(latest) > 100

            if not has_role and not has_jd:
                return Intent.CLARIFY

        # Rule 5: Message contains a job description (long text, usually enough to recommend)
        if len(latest) > 200 or "job description" in latest:
            return Intent.RECOMMEND

        # Fallback: Use Gemini for classification
        return await self._llm_classify(messages)

    async def _llm_classify(self, messages: list[Message]) -> Intent:
        """Use LLM to classify intent when rules are ambiguous."""
        try:
            client = get_llm_client()
            conversation = format_conversation(messages)
            prompt = INTENT_CLASSIFICATION_PROMPT.format(conversation=conversation)

            result = await client.generate_json(
                prompt=prompt,
                system_instruction=SYSTEM_PROMPT,
            )

            intent_str = result.get("intent", "CLARIFY").upper()
            logger.info("LLM classification: %s (reason: %s)", intent_str, result.get("reasoning", ""))

            try:
                return Intent(intent_str)
            except ValueError:
                logger.warning("LLM returned invalid intent: %s, defaulting to CLARIFY", intent_str)
                return Intent.CLARIFY

        except Exception as e:
            logger.error("LLM classification failed: %s, defaulting to CLARIFY", e)
            return Intent.CLARIFY

    async def _dispatch(self, intent: Intent, messages: list[Message]) -> ChatResponse:
        """Dispatch to the appropriate behavior handler."""
        try:
            if intent == Intent.CLARIFY:
                return await handle_clarify(messages)

            elif intent == Intent.RECOMMEND:
                return await handle_recommend(messages, self.retriever, self.catalog)

            elif intent == Intent.REFINE:
                return await handle_refine(messages, self.retriever, self.catalog)

            elif intent == Intent.COMPARE:
                return await handle_compare(messages, self.catalog)

            elif intent == Intent.REFUSE:
                return await handle_refuse(messages)

            else:
                logger.error("Unknown intent: %s", intent)
                return await handle_clarify(messages)

        except Exception as e:
            logger.exception("Error in behavior handler for intent %s: %s", intent, e)
            # Graceful fallback: try to recommend based on what we have
            if intent in (Intent.RECOMMEND, Intent.REFINE):
                return self._fallback_recommend(messages)
            return ChatResponse(
                reply="I encountered an issue processing your request. Could you rephrase what you're looking for?",
                recommendations=[],
                end_of_conversation=False,
            )

    def _has_previous_recommendations(self, messages: list[Message]) -> bool:
        """Check if the assistant has already provided recommendations in this conversation."""
        for msg in messages:
            if msg.role == "assistant":
                # Look for recommendation indicators in previous assistant messages
                indicators = ["recommend", "assessment", "here are", "shortlist", "suggest"]
                if any(ind in msg.content.lower() for ind in indicators):
                    return True
        return False

    def _fallback_recommend(self, messages: list[Message]) -> ChatResponse:
        """Fallback when the full recommend pipeline fails — use direct FAISS search."""
        try:
            query = messages[-1].content
            results = self.retriever.retrieve(query=query, top_k=5)

            if results:
                from app.schemas.response import Recommendation

                recommendations = [
                    Recommendation(
                        name=a.name,
                        url=a.url,
                        test_type=a.test_type_primary,
                    )
                    for a, _ in results[:5]
                ]
                return ChatResponse(
                    reply="Based on your requirements, here are some relevant SHL assessments:",
                    recommendations=recommendations,
                    end_of_conversation=True,
                )
        except Exception:
            pass

        return ChatResponse(
            reply="I had trouble processing your request. Could you tell me more about the role you're hiring for and what skills or traits you'd like to assess?",
            recommendations=[],
            end_of_conversation=False,
        )
