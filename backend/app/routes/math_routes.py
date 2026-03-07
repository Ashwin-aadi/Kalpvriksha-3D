from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.services.math_engine import compute_plot, analyze

router = APIRouter()


class PlotRequest(BaseModel):
    equation: str
    coord_system: str = "cartesian"
    resolution: int = 40
    x_range: List[float] = [-5, 5]
    y_range: List[float] = [-5, 5]


class AnalyzeRequest(BaseModel):
    equation: str
    coord_system: str = "cartesian"
    analysis_type: str = "slope"
    point: List[float] = [0, 0]
    x_range: List[float] = [-5, 5]
    y_range: List[float] = [-5, 5]


@router.post("/math/plot")
def plot_equation(request: PlotRequest):
    result = compute_plot(
        equation=request.equation,
        coord_system=request.coord_system,
        resolution=request.resolution,
        x_range=request.x_range,
        y_range=request.y_range,
    )
    return result


@router.post("/math/analyze")
def analyze_equation(request: AnalyzeRequest):
    result = analyze(
        equation=request.equation,
        coord_system=request.coord_system,
        analysis_type=request.analysis_type,
        point=request.point,
        x_range=request.x_range,
        y_range=request.y_range,
    )
    return result
