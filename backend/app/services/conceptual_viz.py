"""
conceptual_viz.py — Fallback Layer 3
Owner: Ashwin

Handles ABSTRACT and AMBIGUOUS concepts using symbolic metaphor visualization.
Each concept type gets a meaningful metaphorical representation, not a literal one.
"""

import math
from app.models.schemas import ConceptResponse, FallbackResponse, ProceduralShape

C_NAVY   = "#156082"
C_BLUE   = "#0F9ED5"
C_ORANGE = "#E97132"
C_RED    = "#E74C3C"
C_GREEN  = "#2ECC71"
C_AMBER  = "#F39C12"
C_PURPLE = "#9B59B6"
C_TEAL   = "#1ABC9C"
C_GREY   = "#888888"
C_LGREY  = "#BBBBBB"
PALETTE  = [C_RED, C_BLUE, C_GREEN, C_AMBER, C_PURPLE, C_TEAL, C_ORANGE, C_NAVY]


def _s(shape, pos, scale, color, label=None):
    return ProceduralShape(shape=shape, position=list(pos),
                           scale=list(scale), color=color, label=label)

def _sphere(pos, r, color, label=None): return _s("sphere", pos, [r,r,r], color, label)
def _box(pos, sx, sy, sz, color, label=None): return _s("box", pos, [sx,sy,sz], color, label)
def _cone(pos, r, h, color, label=None): return _s("cone", pos, [r,h,r], color, label)

def _edge(x1,y1,z1,x2,y2,z2,color=C_GREY,t=0.05):
    mx,my,mz=(x1+x2)/2,(y1+y2)/2,(z1+z2)/2
    length=math.sqrt((x2-x1)**2+(y2-y1)**2+(z2-z1)**2)+0.001
    return _s("cylinder",[mx,my,mz],[t,length,t],color)


# -- Metaphor 1: Node-Link (hub and spokes) — default --------------------
def _node_link(concept: ConceptResponse) -> list[ProceduralShape]:
    shapes = []
    comps = concept.components[:8] or ["aspect_1","aspect_2","aspect_3"]
    shapes.append(_sphere([0,0,0],1.2,C_NAVY,concept.query[:12]))
    n = len(comps)
    for i,comp in enumerate(comps):
        angle = (2*math.pi/n)*i
        x,z = 3.8*math.cos(angle), 3.8*math.sin(angle)
        shapes.append(_sphere([x,0,z],0.65,PALETTE[i%len(PALETTE)],comp[:10]))
        shapes.append(_edge(0,0,0,x,0,z,C_LGREY))
    return shapes


# -- Metaphor 2: Hierarchy (top-down tree) --------------------------------
def _hierarchy(concept: ConceptResponse) -> list[ProceduralShape]:
    shapes = []
    comps = concept.components[:7] or ["root","level1","level2"]
    shapes.append(_sphere([0,3,0],1.0,C_NAVY,concept.query[:12]))
    for i,comp in enumerate(comps):
        x = (i - len(comps)/2) * 2.2
        shapes.append(_sphere([x,0,0],0.65,PALETTE[i%len(PALETTE)],comp[:10]))
        shapes.append(_edge(0,3,0,x,0,0,C_LGREY))
    return shapes


# -- Metaphor 3: Flow (left-to-right pipeline) ----------------------------
def _flow(concept: ConceptResponse) -> list[ProceduralShape]:
    shapes = []
    comps = concept.components[:6] or ["step_1","step_2","step_3"]
    for i,comp in enumerate(comps):
        x = i*2.6 - len(comps)*1.3
        shapes.append(_box([x,0,0],1.8,0.9,0.9,PALETTE[i%len(PALETTE)],comp[:10]))
        if i < len(comps)-1:
            shapes.append(_edge(x+0.9,0,0,x+1.7,0,0,C_LGREY))
            shapes.append(_cone([x+1.7,0,0],0.2,0.4,C_AMBER))
    return shapes


# -- Metaphor 4: Scale/Balance (justice/equality) -------------------------
def _balance(concept: ConceptResponse) -> list[ProceduralShape]:
    shapes = [
        _s("cylinder",[0,0,0],[0.12,4.0,0.12],C_NAVY),  # pole
        _s("cylinder",[0,2.0,0],[3.2,0.1,0.12],C_AMBER), # beam
        _s("cylinder",[-1.6,1.5,0],[0.08,1.0,0.08],C_GREY),
        _s("cylinder",[1.6,1.5,0],[0.08,1.0,0.08],C_GREY),
        _s("cylinder",[-1.6,1.0,0],[1.2,0.1,1.2],C_BLUE), # left pan
        _s("cylinder",[1.6,1.0,0],[1.2,0.1,1.2],C_BLUE),  # right pan
        _box([0,-2.2,0],0.6,0.3,0.6,C_NAVY,"base"),
    ]
    comps = concept.components[:4]
    for i,comp in enumerate(comps[:2]):
        shapes.append(_sphere([-1.6+i*0.4, 1.25, 0], 0.3, PALETTE[i], comp[:8]))
    return shapes


# -- Metaphor 5: Concentric rings (layers/systems) -----------------------
def _concentric(concept: ConceptResponse) -> list[ProceduralShape]:
    shapes = []
    comps = concept.components[:5] or ["core","layer1","layer2"]
    shapes.append(_sphere([0,0,0],0.8,C_NAVY,comps[0]))
    radii = [2.0,3.2,4.4,5.6]
    colors = [C_BLUE,C_TEAL,C_GREEN,C_AMBER]
    for i,comp in enumerate(comps[1:]):
        r = radii[i]; c = colors[i]
        shapes.append(_s("cylinder",[0,0,0],[r*2,0.08,r*2],c))
        shapes.append(_sphere([r,0,0],0.5,c,comp[:10]))
    return shapes


# -- Metaphor 6: Web/Network (democracy, society) -----------------------
def _network_web(concept: ConceptResponse) -> list[ProceduralShape]:
    shapes = []
    comps = concept.components[:7] or ["node_1","node_2","node_3"]
    n = len(comps)
    positions = []
    for i,comp in enumerate(comps):
        angle = (2*math.pi/n)*i
        r = 3.5 if i > 0 else 0
        x,z = r*math.cos(angle), r*math.sin(angle)
        positions.append((x,0,z))
        color = C_NAVY if i==0 else PALETTE[i%len(PALETTE)]
        size = 0.9 if i==0 else 0.55
        shapes.append(_sphere([x,0,z],size,color,comp[:10]))
    # Connect all to center and a few cross-links
    for i in range(1,n):
        shapes.append(_edge(0,0,0,positions[i][0],0,positions[i][2],C_LGREY))
    for i in range(1,n-1):
        x1,y1,z1=positions[i]; x2,y2,z2=positions[i+1]
        shapes.append(_edge(x1,y1,z1,x2,y2,z2,C_LGREY,0.03))
    return shapes


# -- Metaphor 7: Timeline (history, process, evolution) ------------------
def _timeline(concept: ConceptResponse) -> list[ProceduralShape]:
    comps = concept.components[:6] or ["start","middle","end"]
    shapes = [_s("cylinder",[0,0,0],[0.08,len(comps)*2.5,0.08],C_LGREY)]
    for i,comp in enumerate(comps):
        y = i*2.0 - (len(comps)-1)
        shapes.append(_sphere([0,y,0],0.55,PALETTE[i%len(PALETTE)],comp[:10]))
        shapes.append(_s("cylinder",[0.8,y,0],[0.04,1.2,0.04],C_LGREY))
        shapes.append(_box([1.8,y,0],1.8,0.7,0.5,PALETTE[i%len(PALETTE)],None))
    return shapes


# -- VIZ_RULES mapping ----------------------------------------------------
VIZ_RULES = {
    "democracy":       _network_web,
    "government":      _hierarchy,
    "justice":         _balance,
    "equality":        _balance,
    "love":            _node_link,
    "supply_chain":    _flow,
    "workflow":        _flow,
    "pipeline":        _flow,
    "process":         _flow,
    "freedom":         _node_link,
    "entropy":         _node_link,
    "capitalism":      _hierarchy,
    "socialism":       _network_web,
    "evolution":       _timeline,
    "history":         _timeline,
    "timeline":        _timeline,
    "ecosystem":       _network_web,
    "economy":         _network_web,
    "consciousness":   _concentric,
    "mind":            _concentric,
    "universe":        _concentric,
    "solar_system":    _concentric,
    "energy":          _concentric,
    "power":           _hierarchy,
    "truth":           _balance,
    "beauty":          _node_link,
    "time":            _timeline,
    "society":         _network_web,
    "culture":         _network_web,
    "education":       _hierarchy,
    "knowledge":       _concentric,
}


def generate(concept: ConceptResponse) -> FallbackResponse:
    """
    Entry point for Layer 3. Maps abstract concepts to symbolic metaphors.
    Always returns a FallbackResponse, never None.
    """
    key = concept.query.lower().replace(" ", "_")
    rule_fn = VIZ_RULES.get(key)

    if not rule_fn:
        for rk, fn in VIZ_RULES.items():
            if rk in key or key in rk:
                rule_fn = fn
                break

    if not rule_fn:
        rule_fn = _node_link

    shapes = rule_fn(concept)

    metaphor_name = rule_fn.__name__.replace("_", " ").title()

    return FallbackResponse(
        layer_used=3,
        layer_name="Conceptual Metaphor Visualization",
        result_type="conceptual",
        model=None,
        geometry=shapes,
        explanation=(
            f'"{concept.query}" is an abstract concept — no literal 3D form exists. '
            f"Generated a symbolic {metaphor_name} metaphor: "
            f"central hub represents the concept, surrounded by "
            f"{len(concept.components)} key aspect nodes."
        ),
    )
