from pydantic import BaseModel
from typing import Optional, List


class ConceptRequest(BaseModel):
    query: str


class ConceptResponse(BaseModel):
    query: str
    category: str
    type: str  # physical|biological|algorithmic|abstract|ambiguous
    components: List[str]
    related_terms: List[str]
    spatial_description: str
    search_keywords: List[str]


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
    shape: str  # sphere|cylinder|box|cone
    position: List[float]  # [x, y, z]
    scale: List[float]  # [sx, sy, sz]
    color: str  # hex '#4A90D9'
    label: Optional[str] = None


class FallbackRequest(BaseModel):
    concept: ConceptResponse


class FallbackResponse(BaseModel):
    layer_used: int  # 1, 2, 3, or 4
    layer_name: str
    result_type: str
    model: Optional[ModelResult] = None
    geometry: Optional[List[ProceduralShape]] = None
    explanation: str
