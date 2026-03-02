# Kalpaviraksh-3D 🌐

**Semantic 3D Concept Retrieval & Generation System**

> Team: Ashwin · Ashutosh · Anushree · Vaishnavi

Type any natural language concept — *Human Heart, Binary Search Tree, Democracy, DNA* — and get the best possible 3D representation with AI-powered explanation.

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env   # fill in your API keys (optional — runs without them)
uvicorn app.main:app --reload --port 8000
```

- **API Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

- **App:** http://localhost:5173

---

## No API Keys? No Problem!

The system runs in full **demo mode** without any API keys:

- `llm_service.py` falls back to `_mock_response()` with pre-built concept data for Human Heart, DNA, Solar System, Binary Search Tree, Democracy, and more.
- Layer 2 (procedural geometry) and Layer 3 (conceptual metaphor) generate 3D shapes entirely locally — no external API needed.
- Only Layer 4 (Image-to-3D via Luma AI) requires `LUMA_API_KEY`.

---

## Architecture

```
User Input ──▶ /api/concept  ──▶  LLM extracts structured concept JSON
                                        │
              /api/retrieve  ──▶  Sketchfab + local model_index.json
                                  Cosine similarity ranking
                                        │
                              Confidence ≥ 60%? ──▶ Show 3D model
                                        │
                              Confidence < 60%?
                                        ▼
              /api/fallback  ──▶  Fallback Engine
                                  ├─ Layer 1: Semantic Nearest Match
                                  ├─ Layer 2: Procedural Geometry (Ashwin)
                                  ├─ Layer 3: Conceptual Metaphors (Ashutosh)
                                  └─ Layer 4: Image-to-3D / Luma AI (Ashutosh)
```

## 4 Fallback Layers

| Layer | File | Trigger |
|-------|------|---------|
| 1 – Semantic Nearest | `semantic_nearest.py` | No exact match found |
| 2 – Procedural Geometry | `procedural_gen.py` | Physical/algorithmic concepts |
| 3 – Conceptual Metaphor | `conceptual_viz.py` | Abstract concepts (democracy, entropy) |
| 4 – Image-to-3D | `image_to_3d.py` | User uploads image (requires Luma API key) |

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Deployment

**Backend — Render.com**
```
Build: pip install -r requirements.txt
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Frontend — Vercel**
```
Root: frontend/
Env var: VITE_API_URL = https://your-backend.onrender.com
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI + Uvicorn |
| LLM | OpenAI GPT-4o-mini (mock fallback) |
| Semantic Ranking | Sentence Transformers (all-MiniLM-L6-v2) |
| 3D Retrieval | Sketchfab API + local model_index.json |
| Image-to-3D | Luma AI (optional) |
| Frontend | React 18 + Vite |
| 3D Rendering | Three.js + @react-three/fiber + @react-three/drei |
| HTTP Client | Axios |

---

*Focus > Complexity · Working Demo > Perfect Architecture · Explain It Well > Build Everything*
