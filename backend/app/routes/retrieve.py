from fastapi import APIRouter, HTTPException
from app.models.schemas import RetrieveRequest, RetrieveResponse
from app.services import retrieval_service, ranking_service
import os

router = APIRouter()

THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.60'))


@router.post('/retrieve', response_model=RetrieveResponse)
async def retrieve_models(request: RetrieveRequest) -> RetrieveResponse:
    try:
        concept = request.concept
        candidates = await retrieval_service.search_all(concept)

        if not candidates:
            return RetrieveResponse(models=[], fallback_triggered=True, best_confidence=0.0)

        ranked = ranking_service.rank_models(concept, candidates)
        best = ranked[0].confidence if ranked else 0.0

        return RetrieveResponse(
            models=ranked,
            fallback_triggered=(best < THRESHOLD * 100),
            best_confidence=best
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Retrieval failed: {str(e)}')
