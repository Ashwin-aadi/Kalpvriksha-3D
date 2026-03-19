from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

from app.routes import concept, retrieve, fallback
from app.routes import math_routes, physics_routes

app = FastAPI(
    title="Kalpaviraksh-3D API",
    version="3.0.0",
    description="Semantic 3D Concept Retrieval, Math Grapher & Physics Engine",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core concept explorer
app.include_router(concept.router,        prefix="/api")
app.include_router(retrieve.router,       prefix="/api")
app.include_router(fallback.router,       prefix="/api")

# Math grapher
app.include_router(math_routes.router,    prefix="/api")

# Physics engine
app.include_router(physics_routes.router, prefix="/api")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "3.0.0",
        "modes": ["concept_explorer", "math_grapher", "physics_engine"]
    }