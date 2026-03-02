import os
from app.models.schemas import ConceptResponse, FallbackResponse
from app.services import retrieval_service, ranking_service

THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.60'))


async def find_nearest(concept: ConceptResponse) -> FallbackResponse | None:
    broader = concept.model_copy()
    broader.search_keywords = (
        concept.related_terms +
        [concept.category] +
        concept.components[:3]
    )
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
            layer_name='Semantic Nearest Concept Match',
            result_type='nearest_model',
            model=best,
            geometry=None,
            explanation=(
                f'No exact match for "{concept.query}". '
                f'Nearest semantic match: "{best.title}" '
                f'at {best.confidence:.1f}% confidence. '
                f'Matched: {best.matched_parts}. '
                f'Missing: {best.missing_parts}.'
            ))
    return None  # signal: try next layer
