"""Assessment data model for the SHL catalog."""

from pydantic import BaseModel
from typing import Optional


class Assessment(BaseModel):
    """Represents a single SHL assessment from the product catalog."""

    id: str  # Slug derived from URL
    name: str  # Display name
    url: str  # Full canonical URL on shl.com
    test_type: list[str]  # One or more: A, B, C, D, E, K, P, S
    category: str  # e.g. "Cognitive", "Personality", "Knowledge"
    description: str  # 1-3 sentence description
    duration: Optional[int] = None  # Minutes, None if untimed
    remote_support: bool = True  # Supports remote/online testing
    adaptive_support: bool = False  # Adaptive/IRT scoring
    languages: list[str] = []  # Available languages
    job_levels: list[str] = []  # Applicable job levels

    @property
    def test_type_primary(self) -> str:
        """Return the primary (first) test type code."""
        return self.test_type[0] if self.test_type else "K"

    @property
    def embedding_text(self) -> str:
        """Composite text used for vector embedding."""
        type_names = {
            "A": "Ability & Aptitude",
            "B": "Biodata & Situational Judgment",
            "C": "Competencies",
            "D": "Development & 360",
            "E": "Assessment Exercises",
            "K": "Knowledge & Skills",
            "P": "Personality & Behavior",
            "S": "Simulations",
        }
        types_str = ", ".join(type_names.get(t, t) for t in self.test_type)
        duration_str = f"Duration: {self.duration} minutes." if self.duration else ""
        levels_str = f"Job levels: {', '.join(self.job_levels)}." if self.job_levels else ""

        return (
            f"{self.name}. {self.category}. {self.description} "
            f"Test type: {types_str}. {duration_str} {levels_str}"
        ).strip()
