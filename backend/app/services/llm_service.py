import os
import re
import json
from openai import AsyncOpenAI
from groq import Groq
from app.models.schemas import ConceptResponse

# OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

ALLOWED_TYPES = {'physical', 'biological', 'algorithmic', 'abstract', 'ambiguous'}

SYSTEM_PROMPT = '''You are a 3D concept analyzer. Given any concept, extract structured
information for 3D model retrieval. Respond ONLY with valid JSON:
{
  "category": "short domain label e.g. biological organ",
  "type": "physical|biological|algorithmic|abstract|ambiguous",
  "components": ["list", "of", "key", "structural", "parts"],
  "related_terms": ["synonyms", "related", "keywords"],
  "spatial_description": "one sentence describing 3D shape",
  "search_keywords": ["combined", "list", "for", "sketchfab", "search"]
}'''

def validate_query(query: str) -> str:
    query = re.sub(r'<[^>]+>', '', query)
    query = query.strip()[:200]
    if not query:
        raise ValueError("Query cannot be empty")
    return query

def parse_raw(raw: dict, fallback: bool) -> dict:
    if raw.get('type') not in ALLOWED_TYPES:
        raw['type'] = 'ambiguous'
    raw['fallback_triggered'] = fallback
    return raw
async def extract_concept(query: str) -> ConceptResponse:
    query = validate_query(query)
    print(f"GROQ KEY EXISTS: {bool(os.getenv('GROQ_API_KEY'))}")
    print(f"GROQ KEY VALUE: {os.getenv('GROQ_API_KEY')[:10] if os.getenv('GROQ_API_KEY') else 'NONE'}")

    if not os.getenv('OPENAI_API_KEY') and not os.getenv('GROQ_API_KEY'):
        return _mock_response(query)

    # Try OpenAI first
    if os.getenv('OPENAI_API_KEY'):
        try:
            response = await openai_client.chat.completions.create(
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
            return ConceptResponse(query=query, **parse_raw(raw, False))
        except Exception:
            pass

    # Groq fallback
    if os.getenv('GROQ_API_KEY'):
        try:
            groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            response = groq_client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                response_format={'type': 'json_object'},
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': f'Analyze: {query}'},
                ],
                max_tokens=400,
                temperature=0.1,
            )
            raw = json.loads(response.choices[0].message.content)
            return ConceptResponse(query=query, **parse_raw(raw, False))
        except Exception as e:
            print(f"GROQ ERROR: {e}")
            pass

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