from pydantic import BaseModel
from typing import Optional, List

class ConceptRequest(BaseModel):
    query: str

class ConceptResponse(BaseModel):
    query: str
    category: str
    type: str
    components: List[str]
    related_terms: List[str]
    spatial_description: str
    search_keywords: List[str]
    fallback_triggered: bool = False

class ModelResult(BaseModel):
    id: str
    title: str
    confidence: float
    missing_parts: List[str]
    matched_parts: List[str]
    source: str
    viewer_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class RetrieveRequest(BaseModel):
    concept: ConceptResponse

class RetrieveResponse(BaseModel):
    models: List[ModelResult]
    fallback_triggered: bool
    best_confidence: float

class ProceduralShape(BaseModel):
    shape: str
    position: List[float]
    scale: List[float]
    color: str
    label: Optional[str] = None

class FallbackRequest(BaseModel):
    concept: ConceptResponse

class FallbackResponse(BaseModel):
    layer_used: int
    layer_name: str
    result_type: str
    model: Optional[ModelResult] = None
    geometry: Optional[List[ProceduralShape]] = None
    explanation: str