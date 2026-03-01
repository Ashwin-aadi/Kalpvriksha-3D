"""
test_fallback.py — Automated Tests for the Fallback Engine
Owner: Ashwin

Run with: cd backend && pytest tests/test_fallback.py -v

Tests verify fallback routing without any API keys.
The mock modes in conceptual_viz.py and procedural_gen.py ensure
these pass offline.
"""

import pytest
from app.services import fallback_engine
from app.models.schemas import ConceptResponse

# ── Shared test fixtures ───────────────────────────────────────────────────────

ABSTRACT = ConceptResponse(
    query="Democracy",
    category="political system",
    type="abstract",
    components=["citizens", "voting", "representation"],
    related_terms=["republic"],
    spatial_description="abstract",
    search_keywords=["democracy"],
)

ALGO = ConceptResponse(
    query="Binary Search Tree",
    category="data structure",
    type="algorithmic",
    components=["root", "node", "left_child", "right_child"],
    related_terms=["BST"],
    spatial_description="tree",
    search_keywords=["binary tree"],
)

PHYSICAL = ConceptResponse(
    query="DNA",
    category="biological molecule",
    type="biological",
    components=["base_pair", "helix", "nucleotide", "strand"],
    related_terms=["genetics", "double helix"],
    spatial_description="twisted ladder",
    search_keywords=["dna", "double helix"],
)

# ── Tests ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_never_crashes():
    """Engine must always return a FallbackResponse with a non-empty explanation."""
    result = await fallback_engine.run(ABSTRACT)
    assert result is not None
    assert result.explanation  # non-empty string


@pytest.mark.asyncio
async def test_abstract_hits_layer_3():
    """Abstract concept (Democracy) should route to Layer 3 (conceptual_viz)."""
    result = await fallback_engine.run(ABSTRACT)
    assert result.layer_used == 3
    assert result.result_type == "conceptual"


@pytest.mark.asyncio
async def test_algo_hits_layer_2():
    """Algorithmic concept (BST) should route to Layer 1 or 2 with geometry."""
    result = await fallback_engine.run(ALGO)
    assert result.layer_used in [1, 2]
    assert result.geometry is not None
    assert len(result.geometry) > 0


@pytest.mark.asyncio
async def test_geometry_shapes_valid():
    """All shapes in procedural output must have valid shape types and 3D positions."""
    result = await fallback_engine.run(ALGO)
    valid_shapes = {"sphere", "cylinder", "box", "cone"}
    for shape in result.geometry:
        assert shape.shape in valid_shapes
        assert len(shape.position) == 3
        assert len(shape.scale) == 3


@pytest.mark.asyncio
async def test_layer_name_populated():
    """layer_name must always be a non-empty string."""
    for concept in [ABSTRACT, ALGO, PHYSICAL]:
        result = await fallback_engine.run(concept)
        assert result.layer_name  # non-empty


@pytest.mark.asyncio
async def test_no_result_response_structure():
    """
    If we somehow trigger layer_used=0, the response must still be valid.
    Simulate by passing a concept type with an empty strategy.
    (Requires classifier to return [] for 'unknown' — adjust if classifier differs.)
    """
    unknown = ConceptResponse(
        query="xyzzy",
        category="unknown",
        type="unknown",
        components=[],
        related_terms=[],
        spatial_description="",
        search_keywords=[],
    )
    result = await fallback_engine.run(unknown)
    # Must return a FallbackResponse no matter what
    assert result is not None
    assert isinstance(result.layer_used, int)
    assert result.explanation