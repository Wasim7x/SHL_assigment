"""Load the SHL catalog from JSON file."""

import json
import logging
from pathlib import Path

from app.catalog.models import Assessment

logger = logging.getLogger(__name__)


def load_catalog(catalog_path: str) -> list[Assessment]:
    """Load all assessments from the catalog JSON file."""
    path = Path(catalog_path)
    if not path.exists():
        logger.warning("Catalog file not found at %s, using empty catalog", path)
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assessments = []
    for item in data:
        try:
            assessment = Assessment(**item)
            assessments.append(assessment)
        except Exception as e:
            logger.warning("Skipping invalid catalog entry: %s — %s", item.get("name", "?"), e)

    logger.info("Loaded %d valid assessments from catalog", len(assessments))
    return assessments


def get_catalog_urls(catalog: list[Assessment]) -> set[str]:
    """Get the set of all valid catalog URLs for validation."""
    return {a.url for a in catalog}


def find_assessment_by_name(catalog: list[Assessment], name: str) -> list[Assessment]:
    """Fuzzy search by name — returns assessments whose name contains the query."""
    name_lower = name.lower().strip()
    results = []
    for a in catalog:
        if name_lower in a.name.lower() or a.name.lower() in name_lower:
            results.append(a)
    return results
