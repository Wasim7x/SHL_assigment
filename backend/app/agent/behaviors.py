"""Agent behavior handlers: clarify, recommend, refine, compare, refuse."""

import logging
from typing import Optional

from app.catalog.models import Assessment
from app.catalog.loader import find_assessment_by_name
from app.retrieval.retriever import Retriever
from app.llm.gemini import get_llm_client
from app.agent.prompts import (
    SYSTEM_PROMPT,
    QUERY_BUILDER_PROMPT,
    RECOMMEND_PROMPT,
    REFINE_PROMPT,
    COMPARE_PROMPT,
    CLARIFY_PROMPT,
    REFUSE_PROMPT,
)
from app.schemas.request import Message
from app.schemas.response import ChatResponse, Recommendation
from app.agent.guardrails import validate_recommendations

logger = logging.getLogger(__name__)


def format_conversation(messages: list[Message]) -> str:
    """Format messages into a readable conversation string."""
    lines = []
    for msg in messages:
        prefix = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{prefix}: {msg.content}")
    return "\n".join(lines)


def format_candidates(assessments: list[tuple[Assessment, float]]) -> str:
    """Format retrieved assessments for the LLM prompt."""
    lines = []
    for assessment, score in assessments:
        types_str = ", ".join(assessment.test_type)
        duration_str = f"{assessment.duration} min" if assessment.duration else "untimed"
        lines.append(
            f"- ID: {assessment.id}\n"
            f"  Name: {assessment.name}\n"
            f"  Type: {types_str}\n"
            f"  Category: {assessment.category}\n"
            f"  Description: {assessment.description}\n"
            f"  Duration: {duration_str}\n"
            f"  Remote: {'Yes' if assessment.remote_support else 'No'}\n"
            f"  URL: {assessment.url}\n"
            f"  Score: {score:.3f}"
        )
    return "\n".join(lines)


async def handle_clarify(messages: list[Message]) -> ChatResponse:
    """Ask targeted clarifying questions when not enough info to recommend."""
    client = get_llm_client()
    conversation = format_conversation(messages)

    prompt = CLARIFY_PROMPT.format(conversation=conversation)
    result = await client.generate_json(prompt=prompt, system_instruction=SYSTEM_PROMPT)

    reply = result.get("reply", "Could you tell me more about the role and what you'd like to assess?")

    return ChatResponse(
        reply=reply,
        recommendations=[],
        end_of_conversation=False,
    )


async def handle_recommend(
    messages: list[Message],
    retriever: Retriever,
    catalog: list[Assessment],
) -> ChatResponse:
    """Build query, retrieve, re-rank, and return recommendations."""
    client = get_llm_client()
    conversation = format_conversation(messages)

    # Step 1: Build search query from conversation
    query_prompt = QUERY_BUILDER_PROMPT.format(conversation=conversation)
    query_result = await client.generate_json(
        prompt=query_prompt, system_instruction=SYSTEM_PROMPT
    )

    search_query = query_result.get("query", messages[-1].content)
    filters = query_result.get("filters", {})

    # Step 2: Retrieve candidates
    candidates = retriever.retrieve(
        query=search_query,
        top_k=15,
        filter_types=filters.get("test_types"),
        require_remote=filters.get("require_remote"),
        max_duration=filters.get("max_duration"),
    )

    if not candidates:
        return ChatResponse(
            reply="I couldn't find assessments matching your criteria. Could you provide more details about the role or adjust your requirements?",
            recommendations=[],
            end_of_conversation=False,
        )

    # Step 3: Re-rank with Gemini
    candidates_text = format_candidates(candidates)
    rerank_prompt = RECOMMEND_PROMPT.format(
        conversation=conversation, candidates=candidates_text
    )
    rerank_result = await client.generate_json(
        prompt=rerank_prompt, system_instruction=SYSTEM_PROMPT
    )

    selected_ids = rerank_result.get("selected_ids", [])
    reply = rerank_result.get("reply", "Here are my recommended assessments:")

    # Step 4: Build recommendations from selected IDs
    catalog_map = {a.id: a for a in catalog}
    raw_recs = []
    for aid in selected_ids[:10]:  # Cap at 10
        if aid in catalog_map:
            a = catalog_map[aid]
            raw_recs.append({
                "name": a.name,
                "url": a.url,
                "test_type": a.test_type_primary,
            })

    # Step 5: Validate all URLs against catalog
    validated_recs = validate_recommendations(raw_recs, catalog)

    recommendations = [Recommendation(**r) for r in validated_recs]

    # If no valid recommendations after filtering, fall back to top FAISS results
    if not recommendations and candidates:
        for assessment, _ in candidates[:5]:
            recommendations.append(
                Recommendation(
                    name=assessment.name,
                    url=assessment.url,
                    test_type=assessment.test_type_primary,
                )
            )

    return ChatResponse(
        reply=reply,
        recommendations=recommendations,
        end_of_conversation=True,
    )


async def handle_refine(
    messages: list[Message],
    retriever: Retriever,
    catalog: list[Assessment],
) -> ChatResponse:
    """Refine previous recommendations based on new constraints."""
    client = get_llm_client()
    conversation = format_conversation(messages)

    # Extract previous recommendations from conversation
    previous_recs = ""
    for msg in messages:
        if msg.role == "assistant" and "recommend" in msg.content.lower():
            previous_recs = msg.content
            break

    # Build updated query
    query_prompt = QUERY_BUILDER_PROMPT.format(conversation=conversation)
    query_result = await client.generate_json(
        prompt=query_prompt, system_instruction=SYSTEM_PROMPT
    )

    search_query = query_result.get("query", messages[-1].content)
    filters = query_result.get("filters", {})

    # Retrieve with updated query
    candidates = retriever.retrieve(
        query=search_query,
        top_k=15,
        filter_types=filters.get("test_types"),
        require_remote=filters.get("require_remote"),
        max_duration=filters.get("max_duration"),
    )

    if not candidates:
        return ChatResponse(
            reply="I couldn't find assessments matching your updated criteria. Could you clarify what changes you'd like?",
            recommendations=[],
            end_of_conversation=False,
        )

    # Re-rank with refinement context
    candidates_text = format_candidates(candidates)
    refine_prompt = REFINE_PROMPT.format(
        conversation=conversation,
        previous_recs=previous_recs,
        candidates=candidates_text,
    )
    result = await client.generate_json(
        prompt=refine_prompt, system_instruction=SYSTEM_PROMPT
    )

    selected_ids = result.get("selected_ids", [])
    reply = result.get("reply", "Here are your updated recommendations:")

    # Build and validate recommendations
    catalog_map = {a.id: a for a in catalog}
    raw_recs = []
    for aid in selected_ids[:10]:
        if aid in catalog_map:
            a = catalog_map[aid]
            raw_recs.append({
                "name": a.name,
                "url": a.url,
                "test_type": a.test_type_primary,
            })

    validated_recs = validate_recommendations(raw_recs, catalog)
    recommendations = [Recommendation(**r) for r in validated_recs]

    if not recommendations and candidates:
        for assessment, _ in candidates[:5]:
            recommendations.append(
                Recommendation(
                    name=assessment.name,
                    url=assessment.url,
                    test_type=assessment.test_type_primary,
                )
            )

    return ChatResponse(
        reply=reply,
        recommendations=recommendations,
        end_of_conversation=True,
    )


async def handle_compare(
    messages: list[Message],
    catalog: list[Assessment],
) -> ChatResponse:
    """Compare specific named assessments using catalog data only."""
    client = get_llm_client()
    latest_message = messages[-1].content

    # Find named assessments in the message
    found_assessments = []
    for assessment in catalog:
        name_lower = assessment.name.lower()
        if name_lower in latest_message.lower() or any(
            word in latest_message.lower()
            for word in name_lower.split()
            if len(word) > 3
        ):
            found_assessments.append(assessment)

    # Also try common abbreviations
    abbreviation_map = {
        "opq": "OPQ",
        "gsa": "Global Skills Assessment",
        "mq": "Motivational Questionnaire",
        "sjt": "Situational Judgement",
        "verify": "Verify",
        "ucf": "Universal Competency Framework",
    }
    for abbr, full_name in abbreviation_map.items():
        if abbr in latest_message.lower():
            matches = find_assessment_by_name(catalog, full_name)
            found_assessments.extend(matches)

    # Deduplicate
    seen_ids = set()
    unique_assessments = []
    for a in found_assessments:
        if a.id not in seen_ids:
            seen_ids.add(a.id)
            unique_assessments.append(a)

    if len(unique_assessments) < 2:
        return ChatResponse(
            reply="I couldn't identify the specific assessments you'd like to compare. Could you name them more explicitly? For example: 'Compare OPQ32r and Motivational Questionnaire'.",
            recommendations=[],
            end_of_conversation=False,
        )

    # Format assessments for comparison
    assessments_text = ""
    for a in unique_assessments[:4]:  # Max 4 for comparison
        types_str = ", ".join(a.test_type)
        assessments_text += (
            f"\n---\nName: {a.name}\n"
            f"Category: {a.category}\n"
            f"Type: {types_str}\n"
            f"Description: {a.description}\n"
            f"Duration: {a.duration} min\n"
            f"Remote: {'Yes' if a.remote_support else 'No'}\n"
            f"Adaptive: {'Yes' if a.adaptive_support else 'No'}\n"
        )

    compare_prompt = COMPARE_PROMPT.format(assessments=assessments_text)
    result = await client.generate_json(
        prompt=compare_prompt, system_instruction=SYSTEM_PROMPT
    )

    reply = result.get("reply", "Here's how these assessments compare based on the catalog data.")

    return ChatResponse(
        reply=reply,
        recommendations=[],
        end_of_conversation=False,
    )


async def handle_refuse(messages: list[Message]) -> ChatResponse:
    """Politely refuse an off-topic request."""
    client = get_llm_client()
    latest_message = messages[-1].content

    prompt = REFUSE_PROMPT.format(message=latest_message)
    result = await client.generate_json(
        prompt=prompt, system_instruction=SYSTEM_PROMPT
    )

    reply = result.get(
        "reply",
        "I can only help with SHL assessment recommendations. I can assist you in finding the right assessments for evaluating candidates' skills, personality, cognitive ability, or job-specific competencies. What role or skill area would you like to assess?",
    )

    return ChatResponse(
        reply=reply,
        recommendations=[],
        end_of_conversation=False,
    )
