from fastapi import APIRouter, HTTPException
from app.models.schemas import FallbackRequest, FallbackResponse
from app.services import fallback_engine

router = APIRouter()


@router.post("/fallback", response_model=FallbackResponse,
             summary="Generate 3D when no exact model exists")
async def run_fallback(request: FallbackRequest) -> FallbackResponse:
    try:
        return await fallback_engine.run(request.concept)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallback failed: {str(e)}")
