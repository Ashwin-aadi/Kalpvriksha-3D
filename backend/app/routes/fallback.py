from fastapi import APIRouter, HTTPException
from app.models.schemas import FallbackRequest, FallbackResponse

router = APIRouter()

@router.post('/fallback', response_model=FallbackResponse)
async def run_fallback(request: FallbackRequest) -> FallbackResponse:
    return FallbackResponse(
        layer_used=0,
        layer_name='None',
        result_type='no_result',
        model=None,
        geometry=None,
        explanation='Fallback not implemented yet.'
    )