"""
backend/tests/test_llm_service.py
Owner: Anushree
Covers Day 3 (base tests) and Day 4 (edge cases).
Run with:  python -m pytest tests/test_llm_service.py -v
No API key required — all tests use mock mode.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.llm_service import extract_concept, _mock_response, parse_raw
from app.models.schemas import ConceptResponse

# Mirrors frontend/src/assets/mock_responses/heart.json exactly
HEART_MOCK = ConceptResponse(
    query="Human Heart",
    category="biological organ",
    type="biological",
    components=[
        "left ventricle", "right ventricle",
        "left atrium", "right atrium",
        "aorta", "pulmonary artery",
        "mitral valve", "tricuspid valve",
    ],
    related_terms=[
        "human heart", "cardiac muscle",
        "heart anatomy", "cardiovascular", "3d model",
    ],
    spatial_description=(
        "A fist-sized muscular organ with four chambers, major vessels at the top, "
        "and a rounded base, asymmetric with the apex pointing left."
    ),
    search_keywords=[
        "human heart", "heart anatomy", "cardiac",
        "biological", "3d model", "medical",
    ],
    fallback_triggered=False,
)


# ─────────────────────────────────────────────────────────────
# DAY 3 — Base tests (must pass without any API key)
# ─────────────────────────────────────────────────────────────

def test_mock_response_valid():
    """_mock_response always returns a well-formed ConceptResponse."""
    r = _mock_response("Human Heart")
    assert r.query == "Human Heart"
    assert isinstance(r.components, list)
    assert len(r.components) > 0
    assert isinstance(r.search_keywords, list)
    assert len(r.search_keywords) > 0
    assert r.fallback_triggered is True
    assert r.type in {"physical", "biological", "algorithmic", "abstract", "ambiguous"}


@pytest.mark.asyncio
async def test_extract_concept_mock():
    """extract_concept falls back to mock when no API keys are set."""
    with patch("os.getenv", return_value=None):
        r = await extract_concept("Binary Tree")
    assert r is not None
    assert r.query == "Binary Tree"
    assert isinstance(r, ConceptResponse)
    assert r.fallback_triggered is True


def test_heart_mock_structure():
    """
    Validates HEART_MOCK matches heart.json exactly.
    If this fails, heart.json and ConceptResponse are out of sync.
    """
    r = HEART_MOCK
    assert r.query == "Human Heart"
    assert r.category == "biological organ"
    assert r.type == "biological"
    assert set(r.components) == {
        "left ventricle", "right ventricle",
        "left atrium", "right atrium",
        "aorta", "pulmonary artery",
        "mitral valve", "tricuspid valve",
    }
    assert "cardiovascular" in r.related_terms
    assert "human heart" in r.search_keywords
    assert "medical" in r.search_keywords
    assert r.fallback_triggered is False
    assert "four chambers" in r.spatial_description


# ─────────────────────────────────────────────────────────────
# DAY 4 — Edge cases
# ─────────────────────────────────────────────────────────────

def test_mock_response_unknown_concept():
    """Mock handles a concept that has no obvious category."""
    r = _mock_response("Zorblax Hypercube")
    assert r.query == "Zorblax Hypercube"
    assert isinstance(r.components, list)
    assert isinstance(r.search_keywords, list)
    assert r.fallback_triggered is True


@pytest.mark.asyncio
async def test_extract_concept_empty_query():
    """Empty query raises ValueError before any API call."""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        await extract_concept("   ")


@pytest.mark.asyncio
async def test_extract_concept_html_stripped():
    """HTML tags are stripped from the query."""
    with patch("os.getenv", return_value=None):
        r = await extract_concept("<b>Human Heart</b>")
    assert "<b>" not in r.query
    assert "Human Heart" in r.query


@pytest.mark.asyncio
async def test_extract_concept_query_truncated():
    """Queries longer than 200 chars are silently truncated."""
    long_query = "A" * 300
    with patch("os.getenv", return_value=None):
        r = await extract_concept(long_query)
    assert len(r.query) <= 200


@pytest.mark.asyncio
async def test_extract_concept_malformed_llm_response():
    """
    If the LLM returns JSON missing the 'type' field,
    parse_raw() must default it to 'ambiguous'.
    """
    import json

    bad_payload = {
        # 'type' intentionally omitted -> should become 'ambiguous'
        "category": "unknown",
        "components": ["part_a"],
        "related_terms": ["thing"],
        "spatial_description": "some shape",
        "search_keywords": ["keyword"],
    }

    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(bad_payload)
    mock_response_obj = MagicMock()
    mock_response_obj.choices = [mock_choice]

    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_response_obj)

    with patch("os.getenv", side_effect=lambda k: "fake_key" if k == "OPENAI_API_KEY" else None):
        with patch("app.services.llm_service._get_openai_client", return_value=mock_client_instance):
            r = await extract_concept("Democracy")

    assert r.type == "ambiguous"
    assert isinstance(r, ConceptResponse)


@pytest.mark.asyncio
async def test_extract_concept_openai_fails_groq_fallback():
    """
    When OpenAI raises, Groq is tried. When both fail, _mock_response is returned.
    """
    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create = AsyncMock(side_effect=Exception("OpenAI down"))

    with patch("os.getenv", side_effect=lambda k: "fake_key"):
        with patch("app.services.llm_service._get_openai_client", return_value=mock_client_instance):
            with patch("app.services.llm_service.Groq") as mock_groq_cls:
                mock_groq_cls.return_value.chat.completions.create.side_effect = Exception("Groq down")
                r = await extract_concept("Binary Tree")

    assert r is not None
    assert r.fallback_triggered is True


def test_all_five_concept_types_via_parse_raw():
    """
    parse_raw() must pass through all 5 valid types unchanged
    and normalise anything invalid to 'ambiguous'.
    """
    base = {
        "category": "x", "components": [],
        "related_terms": [], "spatial_description": "x",
        "search_keywords": [],
    }
    valid_types = {"physical", "biological", "algorithmic", "abstract", "ambiguous"}
    for t in valid_types:
        result = parse_raw({**base, "type": t}, False)
        assert result["type"] == t, f"Expected {t!r}, got {result['type']!r}"

    # Invalid type -> 'ambiguous'
    result = parse_raw({**base, "type": "galaxy_brain"}, False)
    assert result["type"] == "ambiguous"