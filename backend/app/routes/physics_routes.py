from fastapi import APIRouter
from pydantic import BaseModel
from app.services.physics_solver import solve
import asyncio

router = APIRouter()


class PhysicsRequest(BaseModel):
    chapter: str
    problem: str


@router.post("/physics/solve")
async def solve_physics(request: PhysicsRequest):
    result = await solve(chapter=request.chapter, problem=request.problem)
    return result
