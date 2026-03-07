"""
semantic_nearest.py — Fallback Layer 1
Owner: Vaishnavi & Anushree

Broadens the search using related terms and category.
If a close-enough model is found (>= THRESHOLD), returns it as Layer 1.
"""

import os
from app.models.schemas import ConceptResponse, FallbackResponse
from app.services import retrieval_service, ranking_service

THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))


async def find_nearest(concept: ConceptResponse) -> FallbackResponse | None:
    """
    Broaden the search using related terms + category + partial components.
    Return a FallbackResponse if any model scores above threshold, else None.
    """
    broader = concept.model_copy()
    broader.search_keywords = (
        concept.related_terms
        + [concept.category]
        + concept.components[:3]
        + concept.search_keywords
    )
    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique_kw: list[str] = []
    for kw in broader.search_keywords:
        if kw.lower() not in seen:
            seen.add(kw.lower())
            unique_kw.append(kw)
    broader.search_keywords = unique_kw[:8]

    candidates = await retrieval_service.search_all(broader)
    if not candidates:
        return None

    ranked = ranking_service.rank_models(concept, candidates)
    if not ranked:
        return None

    best = ranked[0]
    if best.confidence >= THRESHOLD * 100:
        return FallbackResponse(
            layer_used=1,
            layer_name="Semantic Nearest Concept Match",
            result_type="nearest_model",
            model=best,
            geometry=None,
            explanation=(
                f'No exact model for "{concept.query}". '
                f'Nearest semantic match: "{best.title}" '
                f"({best.confidence:.1f}% confidence). "
                f"Matched components: {best.matched_parts}. "
                f"Missing: {best.missing_parts}."
            ),
        )
    return None  # signal: try next layer
