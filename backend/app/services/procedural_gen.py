"""
procedural_gen.py — Fallback Layer 2
Logic:
  1. If CS/algorithmic concept → hardcoded precise generator
  2. Everything else → LLM geometry (Groq llama-3)
  3. LLM fails → _smart_generic
"""

import os, re, json, math, asyncio, concurrent.futures
from app.models.schemas import ConceptResponse, FallbackResponse, ProceduralShape

# DO NOT read env var at module level — read inside functions after dotenv loads
PALETTE = ["#E74C3C","#3498DB","#2ECC71","#F39C12","#9B59B6",
           "#1ABC9C","#E97132","#0F9ED5","#156082","#85C1E9"]
C_BLUE="#0F9ED5"; C_NAVY="#156082"; C_ORANGE="#E97132"; C_RED="#E74C3C"
C_GREEN="#2ECC71"; C_AMBER="#F39C12"; C_PURPLE="#9B59B6"; C_TEAL="#1ABC9C"
C_GREY="#888888"; C_LGREY="#BBBBBB"
DEPTH_COLORS=["#156082","#0F9ED5","#3498DB","#85C1E9","#AED6F1"]

def _s(shape,pos,scale,color,label=None):
    return ProceduralShape(shape=shape,position=list(pos),scale=list(scale),color=color,label=label)
def _sphere(pos,r,color,label=None): return _s("sphere",pos,[r,r,r],color,label)
def _box(pos,sx,sy,sz,color,label=None): return _s("box",pos,[sx,sy,sz],color,label)
def _cone(pos,r,h,color,label=None): return _s("cone",pos,[r,h,r],color,label)
def _cyl(pos,r,h,color,label=None): return _s("cylinder",pos,[r,h,r],color,label)
def _edge(x1,y1,z1,x2,y2,z2,color=C_GREY,t=0.05):
    mx,my,mz=(x1+x2)/2,(y1+y2)/2,(z1+z2)/2
    l=math.sqrt((x2-x1)**2+(y2-y1)**2+(z2-z1)**2)+0.001
    return _s("cylinder",[mx,my,mz],[t,l,t],color)
def _dc(d): return DEPTH_COLORS[min(d,4)]


# ── CS HARDCODED GENERATORS ───────────────────────────────────────────────

def _binary_tree(c):
    shapes=[]
    def add(v,x,y,d):
        if d>3: return
        shapes.append(_sphere([x,y,0],0.55-d*0.05,_dc(d),str(v)))
        sp=2.2/(d+1)
        if d<3:
            lx,rx=x-sp,x+sp
            add(v*2,lx,y-1.7,d+1); add(v*2+1,rx,y-1.7,d+1)
            shapes.append(_edge(x,y,0,lx,y-1.7,0)); shapes.append(_edge(x,y,0,rx,y-1.7,0))
    add(1,0,3,0); return shapes

def _linked_list(c):
    n=max(3,min(6,len(c.components))); shapes=[]
    for i in range(n):
        col=C_ORANGE if i==0 else (C_NAVY if i==n-1 else C_BLUE)
        shapes.append(_sphere([i*2.5,0,0],0.55,col,"HEAD" if i==0 else ("TAIL" if i==n-1 else f"N{i}")))
        if i<n-1:
            shapes.append(_edge(i*2.5,0,0,(i+1)*2.5,0,0))
            shapes.append(_cone([(i+1)*2.5-0.35,0,0],0.18,0.4,C_AMBER))
    return shapes

def _stack(c):
    shapes=[]
    cols=[C_NAVY,C_BLUE,C_BLUE,C_TEAL,C_GREEN]
    for i in range(5):
        shapes.append(_box([0,i*1.1,0],1.8,0.9,0.9,cols[i],"TOP" if i==4 else f"[{i}]"))
    shapes.append(_cyl([0,6.4,0],0.06,0.8,C_GREEN))
    shapes.append(_cone([0,6.9,0],0.2,0.45,C_GREEN,"PUSH"))
    return shapes

def _queue(c):
    shapes=[]
    for i in range(5):
        col=C_RED if i==0 else (C_GREEN if i==4 else C_BLUE)
        shapes.append(_box([i*2.2,0,0],1.8,0.9,0.9,col,"FRONT" if i==0 else ("REAR" if i==4 else f"[{i}]")))
    shapes.append(_cyl([-1.5,0,0],0.06,1.0,C_RED)); shapes.append(_cone([-2.1,0,0],0.2,0.45,C_RED,"DEQ"))
    rx=4*2.2+1.5
    shapes.append(_cyl([rx,0,0],0.06,1.0,C_GREEN)); shapes.append(_cone([rx+0.6,0,0],0.2,0.45,C_GREEN,"ENQ"))
    return shapes

def _neural_network(c):
    layers=[3,5,5,3]; lx=[-4.5,-1.5,1.5,4.5]; lc=[C_TEAL,C_BLUE,C_BLUE,C_ORANGE]
    shapes=[]; npos={}
    for li,(n,x,col) in enumerate(zip(layers,lx,lc)):
        for j in range(n):
            y=(j-(n-1)/2)*1.6
            lbl=f"I{j}" if li==0 else (f"O{j}" if li==3 else f"H{j}")
            shapes.append(_sphere([x,y,0],0.4,col,lbl)); npos[(li,j)]=(x,y)
    for li in range(3):
        for j in range(layers[li]):
            for k in range(layers[li+1]):
                ax,ay=npos[(li,j)]; bx,by=npos[(li+1,k)]
                shapes.append(_edge(ax,ay,0,bx,by,0,C_LGREY,0.025))
    return shapes

def _graph(c):
    nodes=[(0,0,0),(3,2,0),(3,-2,0),(-3,2,0),(-3,-2,0),(0,0,3)]
    edges=[(0,1),(0,2),(0,3),(0,4),(1,2),(3,4),(0,5),(1,5)]
    shapes=[_sphere(list(p),0.5,C_BLUE,f"V{i}") for i,p in enumerate(nodes)]
    for a,b in edges: shapes.append(_edge(*nodes[a],*nodes[b]))
    return shapes

def _hash_table(c):
    shapes=[_box([0,i*1.2,0],2.5,1.0,0.8,C_NAVY,f"[{i}]") for i in range(8)]
    for idx in [1,3,5]: shapes.append(_box([1.5,idx*1.2,0],1.5,0.75,0.6,C_TEAL,"key->val"))
    return shapes

def _matrix(c):
    return [_box([j*1.5-2.25,-i*1.5+2.25,0],1.2,1.2,0.3,C_ORANGE if i==j else C_BLUE,f"[{i},{j}]")
            for i in range(4) for j in range(4)]


# ── CS RULES ─────────────────────────────────────────────────────────────

CS_RULES = {
    "binary_tree":_binary_tree,"binary_search_tree":_binary_tree,"bst":_binary_tree,"tree":_binary_tree,
    "avl_tree":_binary_tree,"red_black_tree":_binary_tree,"heap":_binary_tree,
    "min_heap":_binary_tree,"max_heap":_binary_tree,"priority_queue":_binary_tree,
    "linked_list":_linked_list,"singly_linked_list":_linked_list,
    "doubly_linked_list":_linked_list,"circular_linked_list":_linked_list,
    "stack":_stack,"queue":_queue,"deque":_queue,
    "graph":_graph,"directed_graph":_graph,"undirected_graph":_graph,
    "hash_table":_hash_table,"hash_map":_hash_table,"dictionary":_hash_table,
    "matrix":_matrix,"2d_array":_matrix,"array":_matrix,
    "neural_network":_neural_network,"deep_learning":_neural_network,
}


# ── LLM GEOMETRY PROMPT ──────────────────────────────────────────────────

LLM_GEO_PROMPT = """You are a professional 3D geometry generator for educational visualizations.
Generate a detailed 3D scene for: "{concept}"
Description: {desc}
Key parts: {parts}

Return ONLY raw JSON, no markdown, no explanation:
{{"shapes":[
  {{"shape":"box|sphere|cylinder|cone","position":[x,y,z],"scale":[sx,sy,sz],"color":"#RRGGBB","label":"name or null"}}
]}}

CRITICAL RULES:
1. Generate 10-20 shapes. More = better visualization.
2. Y=0 is ground. Objects sit ON or ABOVE ground (y >= half their height).
3. No two shapes should overlap at exactly the same position.
4. Spread shapes out in 3D space — use x from -6 to 6, y from 0 to 8, z from -4 to 4.
5. Scale guidelines:
   - sphere: scale=[r,r,r] where r=0.2 to 2.0
   - cylinder: scale=[radius,height,radius] — radius=0.05 to 0.8, height=0.3 to 6
   - box: scale=[width,height,depth]
   - cone: scale=[radius,height,radius]
6. Colors must match reality:
   - Biological tissue/organs: reds #E74C3C #C0392B #A93226
   - Bones: #FFFACD
   - Water/veins: #2980B9 #3498DB
   - Stone/marble: #F5F5DC #FFFACD
   - Metal/iron: #8B7355 #708090
   - Green biology: #2ECC71 #27AE60
   - Energy/glow: #F39C12 #E67E22
7. Label only the 6-8 most important parts.
8. Shapes must form a RECOGNIZABLE structure — not random floating objects.

EXAMPLES:

For "Mitochondria":
{{"shapes":[
  {{"shape":"sphere","position":[0,1.2,0],"scale":[2.8,1.6,1.8],"color":"#27AE60","label":"outer membrane"}},
  {{"shape":"sphere","position":[0,1.2,0],"scale":[2.2,1.1,1.3],"color":"#2ECC71","label":"inner membrane"}},
  {{"shape":"sphere","position":[0,1.2,0],"scale":[1.4,0.7,0.9],"color":"#1ABC9C","label":"matrix"}},
  {{"shape":"box","position":[-0.8,1.2,0],"scale":[0.15,0.9,1.1],"color":"#16A085","label":"crista"}},
  {{"shape":"box","position":[0.0,1.2,0],"scale":[0.15,0.9,1.1],"color":"#16A085","label":"crista"}},
  {{"shape":"box","position":[0.8,1.2,0],"scale":[0.15,0.9,1.1],"color":"#16A085","label":"crista"}},
  {{"shape":"sphere","position":[0.5,0.7,0.3],"scale":[0.25,0.25,0.25],"color":"#E74C3C","label":"ATP synthase"}},
  {{"shape":"sphere","position":[-0.5,0.7,-0.3],"scale":[0.25,0.25,0.25],"color":"#E74C3C","label":null}},
  {{"shape":"cylinder","position":[0,1.2,0],"scale":[0.1,1.2,0.1],"color":"#F39C12","label":"mtDNA"}}
]}}

For "Inclined Plane":
{{"shapes":[
  {{"shape":"box","position":[1.5,0.3,0],"scale":[5.0,0.25,2.0],"color":"#95A5A6","label":"ramp surface"}},
  {{"shape":"box","position":[-0.5,0.15,0],"scale":[1.2,0.3,2.0],"color":"#7F8C8D","label":"base support"}},
  {{"shape":"sphere","position":[1.5,0.75,0],"scale":[0.45,0.45,0.45],"color":"#3498DB","label":"object"}},
  {{"shape":"cylinder","position":[1.5,1.5,0],"scale":[0.05,1.4,0.05],"color":"#E74C3C","label":"Fg (gravity)"}},
  {{"shape":"cone","position":[1.5,0.1,0],"scale":[0.12,0.25,0.12],"color":"#E74C3C","label":null}},
  {{"shape":"cylinder","position":[1.9,1.1,0],"scale":[0.05,1.0,0.05],"color":"#2ECC71","label":"FN (normal)"}},
  {{"shape":"cone","position":[2.25,1.55,0],"scale":[0.12,0.25,0.12],"color":"#2ECC71","label":null}},
  {{"shape":"cylinder","position":[0.9,0.85,0],"scale":[0.05,0.8,0.05],"color":"#F39C12","label":"Ff (friction)"}},
  {{"shape":"cone","position":[0.55,0.65,0],"scale":[0.12,0.25,0.12],"color":"#F39C12","label":null}}
]}}

For "Human Heart":
{{"shapes":[
  {{"shape":"sphere","position":[0,1.5,0],"scale":[1.6,1.8,1.4],"color":"#C0392B","label":"heart body"}},
  {{"shape":"sphere","position":[-0.7,2.3,0.5],"scale":[0.85,0.8,0.75],"color":"#E74C3C","label":"left atrium"}},
  {{"shape":"sphere","position":[0.7,2.3,0.5],"scale":[0.8,0.75,0.7],"color":"#E74C3C","label":"right atrium"}},
  {{"shape":"sphere","position":[-0.6,0.8,0.3],"scale":[0.9,1.1,0.85],"color":"#A93226","label":"left ventricle"}},
  {{"shape":"sphere","position":[0.6,0.8,0.3],"scale":[0.85,1.0,0.8],"color":"#B03A2E","label":"right ventricle"}},
  {{"shape":"cylinder","position":[-0.2,3.2,0.1],"scale":[0.22,1.0,0.22],"color":"#C0392B","label":"aorta"}},
  {{"shape":"cylinder","position":[0.4,3.1,0.2],"scale":[0.16,0.85,0.16],"color":"#2980B9","label":"pulmonary artery"}},
  {{"shape":"cylinder","position":[-0.6,3.0,-0.1],"scale":[0.13,0.75,0.13],"color":"#2980B9","label":"vena cava"}},
  {{"shape":"sphere","position":[-0.2,3.7,0.1],"scale":[0.2,0.2,0.2],"color":"#C0392B","label":null}},
  {{"shape":"sphere","position":[0.4,3.65,0.2],"scale":[0.15,0.15,0.15],"color":"#2980B9","label":null}}
]}}

Now generate for: "{concept}"
RETURN ONLY THE JSON OBJECT."""


async def _llm_generate(concept: ConceptResponse):
    """Call Groq to generate geometry. Returns list of ProceduralShape or None."""
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("[procedural_gen] No GROQ_API_KEY found at call time")
        return None
    print(f"[procedural_gen] Calling Groq LLM for '{concept.query}' key={groq_key[:12]}...")
    try:
        import httpx
        prompt = LLM_GEO_PROMPT.format(
            concept=concept.query,
            desc=concept.spatial_description,
            parts=", ".join(concept.components[:8]),
        )
        async with httpx.AsyncClient(timeout=90) as client:
            # Retry up to 3 times on rate limit
            for attempt in range(3):
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}",
                             "Content-Type": "application/json"},
                    json={"model": "llama-3.1-8b-instant",
                          "messages": [{"role": "user", "content": prompt}],
                          "max_tokens": 6000,
                          "temperature": 0.15}
                )
                if resp.status_code == 429:
                    wait = 15 * (attempt + 1)
                    print(f"[procedural_gen] Rate limited, waiting {wait}s (attempt {attempt+1}/3)...")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                break
            else:
                raise ValueError("Groq rate limit exceeded after 3 retries")

            content = resp.json()["choices"][0]["message"]["content"].strip()
            content = re.sub(r"^```(?:json)?", "", content).strip()
            content = re.sub(r"```$", "", content).strip()
            start = content.find("{")
            if start == -1:
                raise ValueError("No JSON object in LLM response")
            json_str = content[start:]

            # Repair truncated JSON — find last complete shape and close arrays
            def repair_json(s):
                last_complete = s.rfind("},")
                if last_complete > 0:
                    return s[:last_complete+1] + "\n]}"
                last_obj = s.rfind("}")
                if last_obj > 0:
                    return s[:last_obj+1] + "\n]}"
                return s

            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                try:
                    data = json.loads(repair_json(json_str))
                except json.JSONDecodeError:
                    data = None
                    for cutoff in range(len(json_str)-1, 100, -200):
                        try:
                            data = json.loads(repair_json(json_str[:cutoff]))
                            break
                        except:
                            continue
                    if data is None:
                        raise ValueError("Could not parse or repair LLM JSON")

            shapes = []
            for item in data.get("shapes", []):
                if not all(k in item for k in ["shape","position","scale","color"]):
                    continue
                if item["shape"] not in ["sphere","cylinder","box","cone"]:
                    continue
                shapes.append(ProceduralShape(
                    shape=item["shape"],
                    position=item["position"],
                    scale=item["scale"],
                    color=item["color"],
                    label=item.get("label"),
                ))
            print(f"[procedural_gen] LLM generated {len(shapes)} shapes for '{concept.query}'")
            return shapes if shapes else None
    except Exception as e:
        print(f"[procedural_gen] LLM geometry failed: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return None


def _smart_generic(concept):
    """Last resort: hub-and-spoke from components."""
    comps = concept.components[:8] or ["core","part_1","part_2"]
    shapes = [_sphere([0,0,0],0.9,C_NAVY,comps[0])]
    inner = comps[1:5]; outer = comps[5:]
    for i,comp in enumerate(inner):
        a=(2*math.pi/max(len(inner),1))*i
        x,z=2.8*math.cos(a),2.8*math.sin(a)
        shapes.append(_sphere([x,0,z],0.55,PALETTE[(i+1)%len(PALETTE)],comp))
        shapes.append(_edge(0,0,0,x,0,z))
    for i,comp in enumerate(outer):
        a=(2*math.pi/max(len(outer),1))*i+math.pi/4
        x,z=5.0*math.cos(a),5.0*math.sin(a)
        shapes.append(_sphere([x,0,z],0.4,PALETTE[(i+3)%len(PALETTE)],comp))
        shapes.append(_edge(0,0,0,x,0,z,C_LGREY))
    return shapes


def _run_async(coro):
    """Run async coroutine safely from sync context."""
    try:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            result = future.result(timeout=120)
            print(f"[procedural_gen] _run_async done, got shapes: {result is not None}")
            return result
    except Exception as e:
        print(f"[procedural_gen] _run_async failed: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        return None


def generate(concept: ConceptResponse) -> FallbackResponse:
    """
    Entry point called by fallback_engine.
    1. CS concept → hardcoded generator
    2. Everything else → LLM geometry
    3. LLM fails → _smart_generic
    """
    key = concept.query.lower().replace(" ","_").replace("-","_")

    # Step 1: CS rules
    rule_fn = CS_RULES.get(key)
    if not rule_fn:
        for rk, fn in CS_RULES.items():
            if rk in key or key in rk:
                rule_fn = fn
                break

    if rule_fn:
        shapes = rule_fn(concept)
        method = "hardcoded"
    else:
        # Step 2: LLM
        print(f"[procedural_gen] No CS rule for '{concept.query}' — calling LLM")
        shapes = _run_async(_llm_generate(concept))
        method = "llm"
        if not shapes:
            # Step 3: last resort
            print(f"[procedural_gen] LLM failed — using smart_generic for '{concept.query}'")
            shapes = _smart_generic(concept)
            method = "generic"

    return FallbackResponse(
        layer_used=2,
        layer_name="Procedural Geometry Generation",
        result_type="procedural",
        model=None,
        geometry=shapes,
        explanation=(
            f'Generated 3D structure for "{concept.query}" using {method} geometry. '
            f"Components: {[s.label for s in shapes if s.label][:6]}."
        ),
    )