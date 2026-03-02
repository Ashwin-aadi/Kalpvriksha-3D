import os
import json
import httpx
from pathlib import Path
from app.models.schemas import ConceptResponse

SKETCHFAB_KEY = os.getenv('SKETCHFAB_API_KEY')
SKETCHFAB_URL = 'https://api.sketchfab.com/v3/models'

# Load model index relative to project root
_index_path = Path(__file__).parents[4] / 'data' / 'model_index.json'
try:
    with open(_index_path, 'r') as f:
        LOCAL_INDEX = json.load(f)['models']
except Exception:
    LOCAL_INDEX = []


async def search_sketchfab(keywords: list[str]) -> list[dict]:
    if not SKETCHFAB_KEY:
        return []
    query = ' '.join(keywords[:3])
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                SKETCHFAB_URL,
                headers={'Authorization': f'Token {SKETCHFAB_KEY}'},
                params={'q': query, 'count': 24, 'sort_by': '-likeCount'})
            resp.raise_for_status()
            results = []
            for item in resp.json().get('results', []):
                results.append({
                    'id': item['uid'],
                    'title': item['name'],
                    'description': item.get('description', ''),
                    'tags': [t['name'] for t in item.get('tags', [])],
                    'viewer_url': f"https://sketchfab.com/models/{item['uid']}/embed",
                    'thumbnail_url': item.get('thumbnails', {}).get('images', [{}])[0].get('url'),
                    'source': 'sketchfab',
                })
            return results
    except Exception:
        return []


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
    seen, combined = set(), []
    for m in (local + sketchfab):
        if m['id'] not in seen:
            seen.add(m['id'])
            combined.append(m)
    return combined
