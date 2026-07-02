"""Evaluate the agent against public conversation traces.

Computes Mean Recall@10 across test traces.

Usage:
    cd backend && python -m scripts.evaluate
"""

import sys
import json
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.catalog.loader import load_catalog
from app.retrieval.vector_store import VectorStore
from app.agent.orchestrator import Orchestrator
from app.schemas.request import Message
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_recall_at_k(recommended: list[str], relevant: list[str], k: int = 10) -> float:
    """Compute Recall@K: fraction of relevant items found in top K recommendations."""
    if not relevant:
        return 1.0  # No relevant items = trivially satisfied

    recommended_set = set(r.lower() for r in recommended[:k])
    relevant_set = set(r.lower() for r in relevant)

    hits = len(recommended_set & relevant_set)
    return hits / len(relevant_set)


async def run_trace(
    orchestrator: Orchestrator,
    trace: dict,
) -> dict:
    """Run a single conversation trace and collect final recommendations."""
    messages = []
    final_recs = []

    # Simulate the conversation from the trace
    for turn in trace.get("conversation", []):
        if turn["role"] == "user":
            messages.append(Message(role="user", content=turn["content"]))

            # Get agent response
            response = await orchestrator.run(messages)
            messages.append(Message(role="assistant", content=response.reply))

            if response.recommendations:
                final_recs = [r.name for r in response.recommendations]

            if response.end_of_conversation:
                break

    return {
        "trace_id": trace.get("id", "unknown"),
        "recommended": final_recs,
        "expected": trace.get("expected_assessments", []),
    }


async def main():
    # Load catalog and build index
    catalog = load_catalog(settings.CATALOG_PATH)
    vector_store = VectorStore.load(settings.FAISS_INDEX_PATH, catalog)

    # Load test traces
    traces_path = Path("data/test_traces.json")
    if not traces_path.exists():
        logger.error("No test traces found at %s", traces_path)
        logger.info("Please add test traces to data/test_traces.json")
        return

    with open(traces_path) as f:
        traces = json.load(f)

    logger.info("Running %d test traces...", len(traces))

    results = []
    for trace in traces:
        orchestrator = Orchestrator(catalog=catalog, vector_store=vector_store)
        result = await run_trace(orchestrator, trace)
        results.append(result)

        recall = compute_recall_at_k(result["recommended"], result["expected"])
        logger.info(
            "Trace '%s': Recall@10 = %.2f (recommended %d, expected %d)",
            result["trace_id"],
            recall,
            len(result["recommended"]),
            len(result["expected"]),
        )

    # Compute mean Recall@10
    recalls = [
        compute_recall_at_k(r["recommended"], r["expected"]) for r in results
    ]
    mean_recall = sum(recalls) / len(recalls) if recalls else 0.0

    print("\n" + "=" * 50)
    print(f"EVALUATION RESULTS")
    print(f"=" * 50)
    print(f"Traces evaluated: {len(results)}")
    print(f"Mean Recall@10: {mean_recall:.4f}")
    print(f"Individual scores: {[f'{r:.2f}' for r in recalls]}")
    print(f"=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
