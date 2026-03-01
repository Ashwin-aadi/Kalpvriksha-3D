"""
fallback_engine.py — Layer Orchestrator
Owner: Ashwin

The brains of the fallback system.
Reads the strategy list for the concept type from classifier.py,
then tries each layer in sequence until one returns a non-None result.

GUARANTEE: Never raises an exception to the caller.
           Always returns a FallbackResponse (layer_used=0 if all layers fail).

NOTE: 'retrieval' in the strategy list is handled upstream by routes/retrieve.py
before /api/fallback is ever called — this file does NOT call retrieval_service.
"""

from app.models.schemas import ConceptResponse, FallbackResponse
from app.services import classifier
from app.services import semantic_nearest, procedural_gen
from app.services import conceptual_viz, image_to_3d


async def run(concept: ConceptResponse) -> FallbackResponse:
    """
    Orchestrates the fallback pipeline.

    1. Gets the ordered strategy list for concept.type from classifier.
    2. Tries each layer in sequence.
    3. Returns the first non-None result.
    4. If all layers fail, returns a safe 'no result' response (layer_used=0).

    Args:
        concept: ConceptResponse — full structured JSON from llm_service.py.

    Returns:
        FallbackResponse — always. layer_used indicates which layer succeeded.
    """
    strategy = classifier.get_strategy(concept.type)
    result: FallbackResponse | None = None

    for layer_name in strategy:
        try:
            if layer_name == "semantic_nearest":
                result = await semantic_nearest.find_nearest(concept)

            elif layer_name == "procedural":
                result = procedural_gen.generate(concept)      # Layer 2

            elif layer_name == "conceptual_viz":
                result = conceptual_viz.generate(concept)       # Layer 3

            elif layer_name == "image_to_3d":
                result = await image_to_3d.generate(concept)   # Layer 4

            else:
                # Unknown layer name — skip silently, don't break the loop
                result = None

        except Exception:
            # Individual layer failure must never crash the engine
            result = None

        if result is not None:
            return result

    # All layers exhausted — return a safe graceful-error response
    return FallbackResponse(
        layer_used=0,
        layer_name="None",
        result_type="no_result",
        model=None,
        geometry=None,
        explanation="Concept could not be represented in 3D. All fallback layers were exhausted.",
    )