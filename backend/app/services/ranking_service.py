"""
ranking_service.py — Smart Title-Match Ranking
Priority:
  1. Exact title match → 95%
  2. All query words in title → 85%
  3. Most query words in title → 75%
  4. Some query words in title → 65%
  5. Semantic similarity (embedder) as tiebreaker
  6. Zero overlap → penalized to 25% (filtered out)
"""

import re
from app.models.schemas import ConceptResponse, ModelResult

_embedder = None
_embedder_available = None


def _get_embedder():
    global _embedder, _embedder_available
    if _embedder_available is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
            _embedder_available = True
        except Exception:
            _embedder_available = False
    return _embedder if _embedder_available else None


def _title_match_score(query: str, title: str) -> float:
    """
    Score based on how well the model title matches the query.
    This is the primary signal — semantic similarity is secondary.
    """
    q = query.lower().strip()
    t = title.lower().strip()

    # Exact match
    if q == t or q in t or t in q:
        return 95.0

    # Tokenize
    q_words = set(re.findall(r"\w+", q)) - {"a", "an", "the", "of", "in", "on", "at", "for", "with"}
    t_words = set(re.findall(r"\w+", t))

    if not q_words:
        return 50.0

    overlap = q_words & t_words
    ratio = len(overlap) / len(q_words)

    if ratio >= 1.0:
        return 88.0   # all query words in title
    elif ratio >= 0.75:
        return 78.0
    elif ratio >= 0.5:
        return 68.0
    elif ratio >= 0.25:
        return 55.0
    elif len(overlap) > 0:
        return 42.0
    else:
        return 20.0   # no overlap — likely wrong model


def _semantic_score(expected_text: str, model_text: str, embedder) -> float:
    """Use sentence embedder for semantic similarity."""
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        expected_vec = embedder.encode([expected_text])
        model_vec = embedder.encode([model_text])
        return round(float(cosine_similarity(expected_vec, model_vec)[0][0]) * 100, 1)
    except Exception:
        return 0.0


def rank_models(concept: ConceptResponse, candidates: list) -> list:
    """
    Rank candidates by relevance to concept.
    Title match is the primary signal. Semantic similarity breaks ties.
    Models with zero title overlap are filtered out unless no better options exist.
    """
    if not candidates:
        return []

    embedder = _get_embedder()
    semantic_text = (
        concept.query + " " +
        " ".join(concept.components[:4]) + " " +
        " ".join(concept.related_terms[:3])
    ).strip()

    ranked = []

    for c in candidates:
        title = c.get("name") or c.get("title") or ""
        title = title.strip()
        title_lower = title.lower()

        # Primary score: title match
        title_score = _title_match_score(concept.query, title)

        # Secondary score: semantic similarity (only if embedder available)
        if embedder and title:
            sem_score = _semantic_score(semantic_text, title, embedder)
            # Blend: 70% title match + 30% semantic
            final_score = round(0.70 * title_score + 0.30 * sem_score, 1)
        else:
            final_score = title_score

        # Hard penalty: if title has zero overlap with query, cap at 30%
        q_words = set(re.findall(r"\w+", concept.query.lower()))
        t_words = set(re.findall(r"\w+", title_lower))
        stopwords = {"a", "an", "the", "of", "in", "on", "at", "for", "with", "and"}
        q_content = q_words - stopwords
        if q_content and not (q_content & t_words):
            final_score = min(final_score, 30.0)

        ranked.append(ModelResult(
            id=c.get("id", ""),
            title=title,
            confidence=final_score,
            matched_parts=[x for x in concept.components if x.lower() in title_lower],
            missing_parts=[x for x in concept.components if x.lower() not in title_lower],
            source=c.get("source", "sketchfab"),
            viewer_url=c.get("embed_url"),
            thumbnail=c.get("thumbnail", ""),
        ))

    ranked.sort(key=lambda x: x.confidence, reverse=True)

    # If best result is penalized (< 35%), still return it but mark low confidence
    # Don't boost bad matches — let fallback handle it
    return ranked