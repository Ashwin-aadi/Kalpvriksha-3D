from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.schemas import ConceptResponse, ModelResult

# Load once at startup — takes ~3 seconds, not per request
EMBEDDER = SentenceTransformer('all-MiniLM-L6-v2')


def rank_models(concept: ConceptResponse, candidates: list[dict]) -> list[ModelResult]:
    if not candidates:
        return []

    expected_text = ' '.join(concept.components + concept.related_terms)
    expected_vec = EMBEDDER.encode([expected_text])

    ranked = []
    for c in candidates:
        model_text = f"{c['title']} {c.get('description', '')} {' '.join(c.get('tags', []))}".strip()
        model_vec = EMBEDDER.encode([model_text])
        score = round(float(cosine_similarity(expected_vec, model_vec)[0][0]) * 100, 1)

        text_lower = model_text.lower()
        ranked.append(ModelResult(
            id=c['id'],
            title=c['title'],
            confidence=score,
            matched_parts=[x for x in concept.components if x.lower() in text_lower],
            missing_parts=[x for x in concept.components if x.lower() not in text_lower],
            source=c.get('source', 'sketchfab'),
            viewer_url=c.get('viewer_url'),
            thumbnail_url=c.get('thumbnail_url'),
        ))

    return sorted(ranked, key=lambda x: x.confidence, reverse=True)
