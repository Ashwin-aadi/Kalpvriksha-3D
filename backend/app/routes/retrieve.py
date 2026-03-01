from fastapi import APIRouter, HTTPException
from app.models.schemas import RetrieveRequest, RetrieveResponse

router = APIRouter()

@router.post('/retrieve', response_model=RetrieveResponse)
async def retrieve_models(request: RetrieveRequest) -> RetrieveResponse:
    return RetrieveResponse(models=[], fallback_triggered=True, best_confidence=0.0)