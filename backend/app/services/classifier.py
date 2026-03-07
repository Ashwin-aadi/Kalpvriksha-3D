"""
classifier.py — Concept Type → Fallback Strategy
Maps concept type to ordered fallback layers.
Note: "retrieval" is handled at the /retrieve route level, not here.
"""

STRATEGIES = {
    "physical":    ["procedural", "semantic_nearest", "image_to_3d"],
    "biological":  ["procedural", "semantic_nearest", "image_to_3d"],
    "algorithmic": ["procedural", "semantic_nearest"],
    "abstract":    ["conceptual_viz", "procedural"],
    "ambiguous":   ["procedural", "semantic_nearest", "conceptual_viz"],
}

def get_strategy(concept_type: str) -> list[str]:
    return STRATEGIES.get(concept_type, STRATEGIES["physical"])

def is_abstract(concept_type: str) -> bool:
    return concept_type == "abstract"

def is_algorithmic(concept_type: str) -> bool:
    return concept_type == "algorithmic"