import pytest
from app.services import fallback_engine
from app.models.schemas import ConceptResponse

ABSTRACT = ConceptResponse(
    query='Democracy', category='political system',
    type='abstract', components=['citizens', 'voting', 'representation'],
    related_terms=['republic'], spatial_description='abstract',
    search_keywords=['democracy'])

ALGO = ConceptResponse(
    query='Binary Search Tree', category='data structure',
    type='algorithmic', components=['root', 'node', 'left_child', 'right_child'],
    related_terms=['BST'], spatial_description='tree',
    search_keywords=['binary tree'])


@pytest.mark.asyncio
async def test_never_crashes():
    result = await fallback_engine.run(ABSTRACT)
    assert result is not None and result.explanation


@pytest.mark.asyncio
async def test_abstract_hits_layer_3():
    result = await fallback_engine.run(ABSTRACT)
    assert result.layer_used == 3
    assert result.result_type == 'conceptual'


@pytest.mark.asyncio
async def test_algo_hits_layer_2():
    result = await fallback_engine.run(ALGO)
    assert result.layer_used in [1, 2]
    assert result.geometry is not None
