import pytest
from app.services.llm_service import extract_concept, _mock_response


def test_mock_response_valid():
    r = _mock_response('Human Heart')
    assert r.query == 'Human Heart'
    assert isinstance(r.components, list)
    assert isinstance(r.search_keywords, list)


def test_mock_response_known_concept():
    r = _mock_response('human heart')
    assert r.type == 'biological'
    assert 'atrium' in r.components


@pytest.mark.asyncio
async def test_extract_concept_mock():
    r = await extract_concept('Binary Tree')
    assert r is not None
    assert r.query == 'Binary Tree'
