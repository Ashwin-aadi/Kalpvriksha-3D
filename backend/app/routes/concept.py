from fastapi import APIRouter, HTTPException
from app.models.schemas import ConceptRequest, ConceptResponse
from app.services import llm_service

router = APIRouter()


@router.post("/concept", response_model=ConceptResponse,
             summary="Extract structured concept from natural language")
async def extract_concept(request: ConceptRequest) -> ConceptResponse:
    try:
        return await llm_service.extract_concept(request.query)
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Concept extraction failed: {str(e)}")
