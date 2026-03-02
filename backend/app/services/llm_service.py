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

MOCK_CONCEPTS = {
    'human heart': {
        'category': 'biological organ', 'type': 'biological',
        'components': ['atrium', 'ventricle', 'valve', 'aorta', 'pulmonary'],
        'related_terms': ['cardiovascular', 'cardiac', 'anatomy'],
        'spatial_description': 'Fist-sized muscular pump with 4 chambers',
        'search_keywords': ['heart', 'anatomy', 'cardiac', 'organ']
    },
    'binary search tree': {
        'category': 'data structure', 'type': 'algorithmic',
        'components': ['root', 'node', 'left_child', 'right_child', 'leaf'],
        'related_terms': ['BST', 'tree', 'sorting', 'algorithm'],
        'spatial_description': 'Hierarchical tree structure with nodes and edges',
        'search_keywords': ['binary tree', 'BST', 'data structure']
    },
    'democracy': {
        'category': 'political system', 'type': 'abstract',
        'components': ['citizens', 'voting', 'representation', 'governance', 'rights'],
        'related_terms': ['republic', 'election', 'parliament'],
        'spatial_description': 'Abstract network of interconnected civic relationships',
        'search_keywords': ['democracy', 'governance', 'voting']
    },
    'eiffel tower': {
        'category': 'monument', 'type': 'physical',
        'components': ['base', 'pillars', 'lattice', 'platform', 'antenna'],
        'related_terms': ['paris', 'france', 'landmark', 'iron tower'],
        'spatial_description': 'Tall iron lattice tower tapering to a point',
        'search_keywords': ['eiffel tower', 'paris', 'landmark', 'france']
    },
    'dna': {
        'category': 'biological molecule', 'type': 'biological',
        'components': ['double helix', 'nucleotide', 'base pair', 'strand', 'backbone'],
        'related_terms': ['genetics', 'chromosome', 'molecule', 'helix'],
        'spatial_description': 'Double helix spiral structure made of nucleotide pairs',
        'search_keywords': ['DNA', 'double helix', 'genetics', 'molecule']
    },
    'solar system': {
        'category': 'astronomical system', 'type': 'physical',
        'components': ['sun', 'planets', 'orbit', 'asteroid belt', 'moons'],
        'related_terms': ['astronomy', 'space', 'planets', 'galaxy'],
        'spatial_description': 'Central star with planets orbiting in elliptical paths',
        'search_keywords': ['solar system', 'planets', 'orbit', 'astronomy']
    },
    'mitochondria': {
        'category': 'cell organelle', 'type': 'biological',
        'components': ['outer membrane', 'inner membrane', 'cristae', 'matrix', 'ATP synthase'],
        'related_terms': ['cell', 'organelle', 'energy', 'ATP'],
        'spatial_description': 'Bean-shaped organelle with folded inner membranes',
        'search_keywords': ['mitochondria', 'cell', 'organelle', 'biology']
    }
}


async def extract_concept(query: str) -> ConceptResponse:
    if not os.getenv('OPENAI_API_KEY'):  # DEMO MODE
        return _mock_response(query)
    response = await client.chat.completions.create(
        model='gpt-4o-mini',
        response_format={'type': 'json_object'},
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': f'Analyze: {query}'},
        ],
        max_tokens=400, temperature=0.1,
    )
    raw = json.loads(response.choices[0].message.content)
    return ConceptResponse(query=query, **raw)


def _mock_response(query: str) -> ConceptResponse:
    key = query.lower().strip()
    if key in MOCK_CONCEPTS:
        return ConceptResponse(query=query, **MOCK_CONCEPTS[key])
    # Generic fallback
    words = query.lower().split()
    return ConceptResponse(
        query=query,
        category='physical object',
        type='physical',
        components=['body', 'structure', 'base', 'surface'],
        related_terms=words + ['3d model', 'object'],
        spatial_description=f'A 3D representation of {query}',
        search_keywords=words + ['3d', 'model'],
    )
