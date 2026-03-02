from app.services import ranking_service
from app.models.schemas import ConceptResponse

CONCEPT = ConceptResponse(
    query='Human Heart', category='biological organ',
    type='biological', components=['atrium', 'ventricle', 'valve', 'aorta'],
    related_terms=['cardiovascular'], spatial_description='4-chamber pump',
    search_keywords=['heart', 'anatomy'])

CANDIDATES = [
    {'id': '1', 'title': 'Human Heart', 'source': 'local',
     'description': '4 chambers atrium ventricle valve aorta', 'tags': ['anatomy']},
    {'id': '2', 'title': 'Apple Fruit', 'source': 'local',
     'description': 'Red apple food snack', 'tags': ['food']},
]


def test_heart_ranks_above_apple():
    ranked = ranking_service.rank_models(CONCEPT, CANDIDATES)
    assert ranked[0].id == '1'
    assert ranked[0].confidence > 50
