# Kalpaviraksh-3D 🌳
### Semantic 3D Concept Retrieval & Generation System

> Type any concept. Get an instant 3D visualization.

**Team:** Ashwin · Ashutosh · Anushree · Vaishnavi

---

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env       # Add your API keys
uvicorn app.main:app --reload --port 8000
# Docs: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
# Open: http://localhost:5173
```

### Tests
```bash
cd backend
PYTHONPATH=. pytest tests/test_fallback.py -v
```

---

## API Keys (all FREE)

| Key | Where to get | Required? |
|-----|-------------|-----------|
| `GROQ_API_KEY` | https://console.groq.com | ✅ Recommended |
| `SKETCHFAB_API_KEY` | https://sketchfab.com/settings#api | Optional |
| `LUMA_API_KEY` | https://lumalabs.ai | Optional (Layer 4) |

**Works without any API keys** — rich mock data + smart generic geometry.

---

## The 4-Layer Fallback System

```
User Query
    │
    ▼
POST /api/concept  ──► Groq LLM (llama-3.1-8b-instant)
    │                  → type, components, keywords
    ▼
POST /api/retrieve ──► Sketchfab API + Local Index
    │                  → ranked models (cosine similarity)
    │
    ├─ confidence ≥ 60%  ──► Direct Model (no badge)
    │
    └─ confidence < 60%  ──► POST /api/fallback
                               │
                               ├─ Layer 1: Semantic Nearest    [Vaishnavi]
                               │   Broaden search, return best match
                               │
                               ├─ Layer 2: Procedural Geometry [Ashwin]
                               │   50+ hardcoded generators + Groq LLM
                               │   for unknown concepts
                               │
                               ├─ Layer 3: Conceptual Metaphor [Ashwin]
                               │   Hub-spoke, hierarchy, flow,
                               │   balance, concentric, timeline
                               │
                               └─ Layer 4: Image-to-3D         [Ashutosh]
                                   Wikipedia image → Luma AI 3D
```

---

## What Can It Visualize?

### Algorithmic (Layer 2)
- Binary Search Tree, AVL, Red-Black Tree, Min/Max Heap
- Linked List, Doubly, Circular, Stack, Queue
- Graph, Directed Graph, Hash Table, Matrix
- Sorting algorithms, Neural Networks

### Physical / Chemical (Layer 2)
- Glucose ring structure, Water molecule, Atom
- DNA double helix, Inclined Plane (with force vectors)
- Solar System, Black Hole, CPU, Eiffel Tower
- Any molecule (via component-based geometry)

### Biological (Layer 2)
- Cell (with organelles), DNA

### Abstract (Layer 3)
- Democracy, Justice, Love, Entropy, Evolution, Ecosystem
- Any concept → symbolic metaphor (hub-spoke, hierarchy, flow, balance)

### Unknown concepts (Layer 2 LLM)
- Groq generates geometry JSON for any concept not in the rules

---

## File Structure

```
kalpaviraksh-3d/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── routes/
│   │   │   ├── concept.py             # POST /api/concept
│   │   │   ├── retrieve.py            # POST /api/retrieve
│   │   │   └── fallback.py            # POST /api/fallback
│   │   ├── services/
│   │   │   ├── llm_service.py         # Groq concept extraction  [Anushree]
│   │   │   ├── classifier.py          # Type → strategy           [Anushree]
│   │   │   ├── retrieval_service.py   # Sketchfab + local         [Vaishnavi]
│   │   │   ├── ranking_service.py     # Cosine similarity         [Vaishnavi]
│   │   │   ├── fallback_engine.py     # Orchestrator              [Ashwin]
│   │   │   ├── semantic_nearest.py    # Layer 1                   [V & A]
│   │   │   ├── procedural_gen.py      # Layer 2 (LLM-enhanced)    [Ashwin]
│   │   │   ├── conceptual_viz.py      # Layer 3                   [Ashwin]
│   │   │   └── image_to_3d.py         # Layer 4                   [Ashutosh]
│   │   └── models/schemas.py
│   ├── tests/test_fallback.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/Home.jsx             # Main page
│       ├── components/
│       │   ├── Viewer3D.jsx           # Three.js viewer
│       │   ├── SearchBar.jsx          # Search + suggestions
│       │   ├── ExplanationPanel.jsx   # AI analysis sidebar
│       │   ├── FallbackBadge.jsx      # Layer indicator
│       │   └── LoadingScreen.jsx      # Animated loading
│       ├── hooks/useModelLoader.js    # Search state machine
│       └── services/api.js
├── data/
│   ├── model_index.json              # Local model catalogue
│   └── concept_map.json              # Keyword mappings
└── .env.example
```

---

## Deployment

**Backend → Render.com**
```
Build: pip install -r requirements.txt
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Frontend → Vercel**
```
Framework: Vite
Root: frontend/
Env: VITE_API_URL=https://your-backend.onrender.com
```
