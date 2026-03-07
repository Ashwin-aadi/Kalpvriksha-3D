from fastapi import APIRouter
from app.models.schemas import RetrieveRequest, RetrieveResponse, ModelResult
from app.services.retrieval_service import retrieve
from app.services.ranking_service import rank_models

router = APIRouter()

import os
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "40.0"))

@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_models(request: RetrieveRequest):
    concept = request.concept
    raw_results = await retrieve(concept)

    if not raw_results:
        return RetrieveResponse(
            models=[],
            fallback_triggered=True,
            best_confidence=0.0,
        )

    ranked = rank_models(concept, raw_results)
    raw_by_id = {r["id"]: r for r in raw_results}

    models = []
    for r in ranked:
        raw = raw_by_id.get(r.id, {})
        embed_url = raw.get("embed_url")
        models.append(ModelResult(
            id=r.id,
            title=r.title,
            viewer_url=embed_url,
            embed_url=embed_url,
            thumbnail=raw.get("thumbnail", ""),
            confidence=r.confidence,
            source=r.source,
            matched_parts=r.matched_parts,
            missing_parts=r.missing_parts,
            is_sketchfab=raw.get("source") == "sketchfab",
        ))

    best_confidence = models[0].confidence if models else 0.0
    fallback_triggered = best_confidence < CONFIDENCE_THRESHOLD

    return RetrieveResponse(
        models=models,
        fallback_triggered=fallback_triggered,
        best_confidence=best_confidence,
    )