"""
fallback_engine.py — Orchestrates all 4 fallback layers
"""
import asyncio
from app.models.schemas import ConceptResponse, FallbackResponse
from app.services import classifier
from app.services import semantic_nearest, procedural_gen
from app.services import conceptual_viz, image_to_3d


async def run(concept: ConceptResponse) -> FallbackResponse:
    strategy = classifier.get_strategy(concept.type)

    for layer_name in strategy:
        try:
            result = None

            if layer_name == "semantic_nearest":
                result = await semantic_nearest.find_nearest(concept)

            elif layer_name == "procedural":
                # generate() is sync but calls _run_async internally.
                # Run it in a thread to avoid blocking the event loop.
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, procedural_gen.generate, concept
                )

            elif layer_name == "conceptual_viz":
                result = conceptual_viz.generate(concept)

            elif layer_name == "image_to_3d":
                result = await image_to_3d.generate(concept)

            elif layer_name == "retrieval":
                # retrieval is handled at the route level before fallback is called
                # skip it here silently
                continue

            if result is not None:
                return result

        except Exception as e:
            print(f"[fallback_engine] Layer '{layer_name}' failed: {e}")
            import traceback
            traceback.print_exc()
            continue

    return FallbackResponse(
        layer_used=0,
        layer_name="None",
        result_type="no_result",
        model=None,
        geometry=None,
        explanation=(
            f'Could not generate a 3D representation for "{concept.query}". '
            "Please try a more specific description."
        ),
    )