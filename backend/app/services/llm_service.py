import os
import json
from openai import AsyncOpenAI
from app.models.schemas import ConceptResponse

client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SYSTEM_PROMPT = '''
You are a 3D concept analyzer. Given any concept, extract structured
information for 3D model retrieval. Respond ONLY with valid JSON:
{
  "category": "short domain label e.g. biological organ",
  "type": "physical|biological|algorithmic|abstract|ambiguous",
  "components": ["list", "of", "key", "structural", "parts"],
  "related_terms": ["synonyms", "related", "keywords"],
  "spatial_description": "one sentence describing 3D shape",
  "search_keywords": ["combined", "list", "for", "sketchfab", "search"]
}'''

async def extract_concept(query: str) -> ConceptResponse:
    if not os.getenv('OPENAI_API_KEY'):  # DEMO MODE
        return _mock_response(query)
    try:
        response = await client.chat.completions.create(
            model='gpt-4o-mini',
            response_format={'type': 'json_object'},
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f'Analyze: {query}'},
            ],
            max_tokens=400,
            temperature=0.1,
        )
        raw = json.loads(response.choices[0].message.content)
        return ConceptResponse(query=query, **raw)
    except Exception:
        return _mock_response(query)

def _mock_response(query: str) -> ConceptResponse:
    return ConceptResponse(
        query=query,
        category='physical object',
        type='physical',
        components=['body', 'structure', 'base'],
        related_terms=[query.lower(), '3d model'],
        spatial_description=f'A 3D representation of {query}',
        search_keywords=[query.lower(), '3d', 'model'],
        fallback_triggered=True,
    )