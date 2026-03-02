from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.routes import concept, retrieve, fallback

app = FastAPI(title='Kalpaviraksh-3D API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(concept.router, prefix='/api')
app.include_router(retrieve.router, prefix='/api')
app.include_router(fallback.router, prefix='/api')

@app.get('/health')
def health_check():
    return {'status': 'ok', 'message': 'Kalpaviraksh-3D is running'}

# Start: uvicorn app.main:app --reload --port 8000
# Docs: http://localhost:8000/docs
