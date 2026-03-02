import pytest
from app.services import retrieval_service
from app.models.schemas import ConceptResponse

MOCK = ConceptResponse(
    query='Human Heart', category='biological organ',
    type='biological', components=['atrium', 'ventricle', 'valve'],
    related_terms=['cardiovascular'], spatial_description='4-chamber pump',
    search_keywords=['heart', 'anatomy'])


def test_local_search_returns_list():
    results = retrieval_service.search_local(['heart', 'anatomy'])
    assert isinstance(results, list)


def test_local_search_finds_heart():
    results = retrieval_service.search_local(['heart', 'anatomy'])
    ids = [r['id'] for r in results]
    assert 'local_heart_001' in ids


@pytest.mark.asyncio
async def test_search_all_returns_list():
    results = await retrieval_service.search_all(MOCK)
    assert isinstance(results, list)
    assert len(results) > 0
