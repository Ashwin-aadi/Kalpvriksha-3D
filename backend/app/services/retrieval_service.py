import os
import json
import httpx
from app.models.schemas import ConceptResponse

SKETCHFAB_KEY = os.getenv('SKETCHFAB_API_KEY')
SKETCHFAB_URL = 'https://api.sketchfab.com/v3/models'

# Load local index once at startup
with open('data/model_index.json', 'r') as f:
    LOCAL_INDEX = json.load(f)['models']


async def search_sketchfab(keywords: list[str]) -> list[dict]:
    if not SKETCHFAB_KEY:
        return []  # skip silently if no API key
    query = ' '.join(keywords[:3])
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            SKETCHFAB_URL,
            headers={'Authorization': f'Token {SKETCHFAB_KEY}'},
            params={'q': query, 'count': 24, 'sort_by': '-likeCount'}
        )
        resp.raise_for_status()
        results = []
        for item in resp.json().get('results', []):
            results.append({
                'id': item['uid'],
                'title': item['name'],
                'description': item.get('description', ''),
                'tags': [t['name'] for t in item.get('tags', [])],
                'viewer_url': f"https://sketchfab.com/models/{item['uid']}/embed",
                'source': 'sketchfab',
            })
        return results


def search_local(keywords: list[str]) -> list[dict]:
    kw = [k.lower() for k in keywords]
    results = []
    for model in LOCAL_INDEX:
        combined = (model['title'] + ' ' + ' '.join(model.get('tags', []))).lower()
        matches = sum(1 for k in kw if k in combined)
        if matches > 0:
            results.append({**model, 'match_count': matches})
    return sorted(results, key=lambda x: x['match_count'], reverse=True)


async def search_all(concept: ConceptResponse) -> list[dict]:
    sketchfab = await search_sketchfab(concept.search_keywords)
    local = search_local(concept.search_keywords)
    # deduplicate, local results come first
    seen, combined = set(), []
    for m in (local + sketchfab):
        if m['id'] not in seen:
            seen.add(m['id'])
            combined.append(m)
    return combined