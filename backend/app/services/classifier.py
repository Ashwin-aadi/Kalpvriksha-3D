STRATEGIES = {
    'physical':    ['retrieval', 'semantic_nearest', 'procedural', 'image_to_3d'],
    'biological':  ['retrieval', 'semantic_nearest', 'procedural', 'image_to_3d'],
    'algorithmic': ['procedural', 'retrieval', 'semantic_nearest'],
    'abstract':    ['conceptual_viz'],
    'ambiguous':   ['retrieval', 'semantic_nearest', 'conceptual_viz'],
}

def get_strategy(concept_type: str) -> list[str]:
    return STRATEGIES.get(concept_type, STRATEGIES['physical'])

def is_abstract(concept_type: str) -> bool:
    return concept_type == 'abstract'