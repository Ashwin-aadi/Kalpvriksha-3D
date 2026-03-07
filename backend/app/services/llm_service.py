"""
llm_service.py — Concept Extraction
Owner: Anushree

Uses Groq (FREE, fast llama-3) for concept extraction.
Falls back to rich mock data if no API key is set.
"""

import os
import json
from app.models.schemas import ConceptResponse

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SYSTEM_PROMPT = """You are a 3D concept analyzer. Given any concept, extract structured
information for 3D model retrieval and generation.
Respond ONLY with valid JSON — no markdown, no explanation, just raw JSON:
{
  "category": "short domain label e.g. biological organ",
  "type": "physical|biological|algorithmic|abstract|ambiguous",
  "components": ["list", "of", "key", "structural", "parts", "max 8"],
  "related_terms": ["synonyms", "related", "keywords", "max 6"],
  "spatial_description": "one sentence describing the 3D shape or structure",
  "search_keywords": ["combined", "list", "for", "sketchfab", "search", "max 6"]
}

Rules:
- type must be exactly one of: physical, biological, algorithmic, abstract, ambiguous
- components should be the actual structural parts (e.g. for glucose: carbon, hydrogen, oxygen, ring, bond)
- For abstract concepts (love, democracy, entropy) use type=abstract
- For data structures, algorithms use type=algorithmic
- For molecules, physics use type=physical
- For cells, organs, DNA use type=biological"""

# Rich mock data for demo mode (no API key needed)
MOCK_CONCEPTS = {
    "human heart": {
        "category": "biological organ", "type": "biological",
        "components": ["left atrium", "right atrium", "left ventricle", "right ventricle", "aorta", "valve"],
        "related_terms": ["cardiovascular", "cardiac", "anatomy", "pump"],
        "spatial_description": "Fist-sized muscular pump with 4 chambers arranged around a central axis",
        "search_keywords": ["heart", "anatomy", "cardiac", "organ", "biology"]
    },
    "binary search tree": {
        "category": "data structure", "type": "algorithmic",
        "components": ["root", "node", "left_child", "right_child", "leaf", "edge"],
        "related_terms": ["BST", "tree", "sorting", "algorithm", "search"],
        "spatial_description": "Hierarchical inverted tree with root at top, branching down",
        "search_keywords": ["binary tree", "BST", "data structure", "algorithm"]
    },
    "bst": {
        "category": "data structure", "type": "algorithmic",
        "components": ["root", "node", "left_child", "right_child", "leaf", "edge"],
        "related_terms": ["binary search tree", "tree", "sorting"],
        "spatial_description": "Hierarchical inverted tree with root at top",
        "search_keywords": ["binary tree", "BST", "data structure"]
    },
    "democracy": {
        "category": "political system", "type": "abstract",
        "components": ["citizens", "voting", "representation", "governance", "rights", "elections"],
        "related_terms": ["republic", "election", "parliament", "freedom"],
        "spatial_description": "Abstract network of interconnected civic relationships radiating from a central hub",
        "search_keywords": ["democracy", "governance", "voting", "political"]
    },
    "glucose": {
        "category": "organic molecule", "type": "physical",
        "components": ["carbon", "hydrogen", "oxygen", "ring", "hydroxyl", "aldehyde"],
        "related_terms": ["C6H12O6", "sugar", "carbohydrate", "monosaccharide"],
        "spatial_description": "Six-membered pyranose ring with carbon backbone and hydroxyl groups",
        "search_keywords": ["glucose", "sugar", "molecule", "chemistry", "C6H12O6"]
    },
    "water molecule": {
        "category": "inorganic molecule", "type": "physical",
        "components": ["oxygen", "hydrogen", "bond", "lone pair"],
        "related_terms": ["H2O", "water", "molecule", "chemistry"],
        "spatial_description": "Bent V-shaped molecule with oxygen at center and two hydrogen atoms",
        "search_keywords": ["water", "H2O", "molecule", "chemistry"]
    },
    "dna": {
        "category": "biological molecule", "type": "biological",
        "components": ["double helix", "nucleotide", "base pair", "strand", "backbone", "adenine", "thymine"],
        "related_terms": ["genetics", "chromosome", "molecule", "helix", "RNA"],
        "spatial_description": "Double helix spiral structure wound around a central axis",
        "search_keywords": ["DNA", "double helix", "genetics", "molecule"]
    },
    "solar system": {
        "category": "astronomical system", "type": "physical",
        "components": ["sun", "mercury", "venus", "earth", "mars", "jupiter", "saturn", "orbit"],
        "related_terms": ["astronomy", "space", "planets", "galaxy", "cosmos"],
        "spatial_description": "Central star with 8 planets orbiting in elliptical paths at varying distances",
        "search_keywords": ["solar system", "planets", "orbit", "astronomy"]
    },
    "mitochondria": {
        "category": "cell organelle", "type": "biological",
        "components": ["outer membrane", "inner membrane", "cristae", "matrix", "ATP synthase"],
        "related_terms": ["cell", "organelle", "energy", "ATP", "powerhouse"],
        "spatial_description": "Bean-shaped organelle with folded inner membrane cristae",
        "search_keywords": ["mitochondria", "cell", "organelle", "biology"]
    },
    "inclined plane": {
        "category": "simple machine", "type": "physical",
        "components": ["ramp", "surface", "angle", "normal force", "gravity", "friction"],
        "related_terms": ["simple machine", "physics", "slope", "wedge", "mechanical advantage"],
        "spatial_description": "Tilted flat surface at an angle with force vectors acting on an object",
        "search_keywords": ["inclined plane", "ramp", "physics", "simple machine"]
    },
    "stack": {
        "category": "data structure", "type": "algorithmic",
        "components": ["top", "push", "pop", "element", "base", "pointer"],
        "related_terms": ["LIFO", "data structure", "queue", "algorithm"],
        "spatial_description": "Vertical tower of stacked elements with access only at the top",
        "search_keywords": ["stack", "data structure", "LIFO", "algorithm"]
    },
    "linked list": {
        "category": "data structure", "type": "algorithmic",
        "components": ["head", "node", "data", "next pointer", "tail", "null"],
        "related_terms": ["list", "pointer", "data structure", "chain"],
        "spatial_description": "Linear chain of nodes each pointing to the next",
        "search_keywords": ["linked list", "data structure", "pointer"]
    },
    "neural network": {
        "category": "machine learning model", "type": "algorithmic",
        "components": ["input layer", "hidden layer", "output layer", "neuron", "weight", "bias"],
        "related_terms": ["deep learning", "AI", "perceptron", "backpropagation"],
        "spatial_description": "Layered network of connected circular nodes with weighted edges",
        "search_keywords": ["neural network", "deep learning", "AI", "machine learning"]
    },
    "black hole": {
        "category": "astronomical object", "type": "physical",
        "components": ["singularity", "event horizon", "accretion disk", "photon sphere", "jet"],
        "related_terms": ["gravity", "space", "relativity", "singularity", "Hawking"],
        "spatial_description": "Spherical event horizon surrounded by a glowing accretion disk",
        "search_keywords": ["black hole", "space", "gravity", "astronomy"]
    },
    "eiffel tower": {
        "category": "monument", "type": "physical",
        "components": ["base", "first floor", "second floor", "summit", "lattice", "pillars"],
        "related_terms": ["paris", "france", "landmark", "iron tower", "architecture"],
        "spatial_description": "Tall tapered iron lattice tower with 4 curved legs meeting at apex",
        "search_keywords": ["eiffel tower", "paris", "landmark", "france"]
    },
    "cube": {
        "category": "geometric shape", "type": "physical",
        "components": ["face", "edge", "vertex", "diagonal"],
        "related_terms": ["hexahedron", "box", "square", "3D shape"],
        "spatial_description": "Six equal square faces meeting at right angles",
        "search_keywords": ["cube", "geometry", "3D shape", "hexahedron"]
    },
    "cell": {
        "category": "biological cell", "type": "biological",
        "components": ["nucleus", "membrane", "cytoplasm", "mitochondria", "ribosome", "golgi"],
        "related_terms": ["biology", "organelle", "eukaryote", "prokaryote"],
        "spatial_description": "Spherical container with internal organelles suspended in cytoplasm",
        "search_keywords": ["cell", "biology", "organelle", "nucleus"]
    },
    "atom": {
        "category": "atomic structure", "type": "physical",
        "components": ["nucleus", "proton", "neutron", "electron", "electron shell", "orbital"],
        "related_terms": ["chemistry", "quantum", "element", "particle"],
        "spatial_description": "Dense central nucleus surrounded by electron shells in orbital paths",
        "search_keywords": ["atom", "nucleus", "electron", "chemistry"]
    },
}


async def extract_concept(query: str) -> ConceptResponse:
    """Extract structured concept. Uses Groq if key set, else rich mock data."""
    if GROQ_API_KEY:
        try:
            return await _groq_extract(query)
        except Exception as e:
            print(f"[llm_service] Groq failed ({e}), falling back to mock")
    return _mock_response(query)


async def _groq_extract(query: str) -> ConceptResponse:
    """Call Groq API (llama-3.1-8b-instant — free tier)."""
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this concept for 3D visualization: {query}"},
                ],
                "max_tokens": 500,
                "temperature": 0.1,
            }
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        raw = json.loads(content.strip())
        return ConceptResponse(query=query, **raw)


def _mock_response(query: str) -> ConceptResponse:
    """Rich mock response — works with no API key."""
    key = query.lower().strip()
    if key in MOCK_CONCEPTS:
        return ConceptResponse(query=query, **MOCK_CONCEPTS[key])
    # Smart generic fallback based on keywords
    words = query.lower().split()
    concept_type = _guess_type(words)
    components = _guess_components(query, words)
    return ConceptResponse(
        query=query,
        category=_guess_category(words),
        type=concept_type,
        components=components,
        related_terms=words[:4] + ["3d model", "visualization"],
        spatial_description=f"A 3D structural representation of {query}",
        search_keywords=words[:4] + ["3d", "model"],
    )


def _guess_type(words: list[str]) -> str:
    algo_kw = {"tree", "graph", "stack", "queue", "list", "sort", "search",
               "hash", "heap", "algorithm", "network", "binary", "linked"}
    bio_kw = {"cell", "dna", "rna", "protein", "organ", "tissue", "bacteria",
              "virus", "chromosome", "membrane", "enzyme", "heart", "brain"}
    abstract_kw = {"love", "democracy", "freedom", "justice", "entropy",
                   "time", "consciousness", "evil", "beauty", "truth"}
    w = set(words)
    if w & algo_kw:
        return "algorithmic"
    if w & bio_kw:
        return "biological"
    if w & abstract_kw:
        return "abstract"
    return "physical"


def _guess_category(words: list[str]) -> str:
    if any(w in words for w in ["molecule", "atom", "chemical", "compound"]):
        return "chemical structure"
    if any(w in words for w in ["tree", "graph", "list", "stack", "queue"]):
        return "data structure"
    if any(w in words for w in ["cell", "organ", "tissue", "protein"]):
        return "biological structure"
    return "physical object"


def _guess_components(query: str, words: list[str]) -> list[str]:
    if len(words) == 1:
        return ["body", "surface", "core", "structure"]
    return [w for w in words if len(w) > 2][:6] or ["component_1", "component_2", "component_3"]
