import math
from app.models.schemas import ConceptResponse, FallbackResponse, ProceduralShape

def generate(concept: ConceptResponse) -> FallbackResponse:
    comps = concept.components[:6] or ['aspect_1', 'aspect_2', 'aspect_3']
    shapes = []
    shapes.append(ProceduralShape(shape='sphere', position=[0, 0, 0],
                                  scale=[1.2, 1.2, 1.2], color='#156082',
                                  label=concept.query))
    for i, comp in enumerate(comps):
        angle = (2 * math.pi / len(comps)) * i
        x, z = 3.0 * math.cos(angle), 3.0 * math.sin(angle)
        shapes.append(ProceduralShape(shape='sphere', position=[x, 0, z],
                                      scale=[0.7, 0.7, 0.7], color='#E97132',
                                      label=comp))
        shapes.append(ProceduralShape(shape='cylinder', position=[x*.5, 0, z*.5],
                                      scale=[0.05, 3.0, 0.05], color='#AAAAAA'))
    return FallbackResponse(
        layer_used=3, layer_name='Conceptual Metaphor Visualization',
        result_type='conceptual', model=None, geometry=shapes,
        explanation=(f'"{concept.query}" is abstract. '
                     f'Generated a symbolic node-link metaphor.'))