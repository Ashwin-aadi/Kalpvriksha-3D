from app.models.schemas import ConceptResponse, FallbackResponse
from app.services import classifier
from app.services import semantic_nearest, procedural_gen
from app.services import conceptual_viz, image_to_3d


async def run(concept: ConceptResponse) -> FallbackResponse:
    strategy = classifier.get_strategy(concept.type)
    for layer_name in strategy:
        result = None
        if layer_name == 'semantic_nearest':
            result = await semantic_nearest.find_nearest(concept)
        elif layer_name == 'procedural':
            result = procedural_gen.generate(concept)
        elif layer_name == 'conceptual_viz':
            result = conceptual_viz.generate(concept)
        elif layer_name == 'image_to_3d':
            result = await image_to_3d.generate(concept)
        if result:
            return result
    return FallbackResponse(
        layer_used=0,
        layer_name='None',
        result_type='no_result',
        model=None,
        geometry=None,
        explanation='Concept could not be represented in 3D.')
