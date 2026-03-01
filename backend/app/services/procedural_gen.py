"""
procedural_gen.py — Fallback Layer 2
Owner: Ashwin

Handles PHYSICAL and ALGORITHMIC concepts only.
Generates geometry using rule-based primitives (spheres, cylinders, boxes).
Returns a FallbackResponse with a geometry list that Three.js can render.
COMPLETELY SEPARATE from conceptual_viz.py (Ashutosh's Layer 3).

The RULES dict maps concept names → specialized generator functions.
Add new entries here to support more concept types without touching the engine.
"""

import math
from app.models.schemas import ConceptResponse, FallbackResponse, ProceduralShape


def generate(concept: ConceptResponse) -> FallbackResponse:
    """
    Entry point called by fallback_engine.py when strategy includes 'procedural'.
    Normalises the concept query to a snake_case key and looks it up in RULES.
    Falls back to concept.type as key, then _generic() if nothing matches.
    Never returns None — always produces at least a generic row of spheres.
    """
    key = concept.query.lower().replace(" ", "_")
    rule_fn = RULES.get(key) or RULES.get(concept.type)
    shapes = rule_fn(concept) if rule_fn else _generic(concept)

    return FallbackResponse(
        layer_used=2,
        layer_name="Procedural Geometry Generation",
        result_type="procedural",
        model=None,
        geometry=shapes,
        explanation=(
            f'No matching model for "{concept.query}". '
            f"Generated structural approximation using geometric primitives. "
            f"Components: {[s.label for s in shapes if s.label]}."
        ),
    )


# ── Generator functions ────────────────────────────────────────────────────────

def _binary_tree(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Builds a recursive BST up to depth 3.
    Nodes are spheres (#0F9ED5), edges are thin grey cylinders.
    Respects left/right child positions and depth levels.
    """
    shapes = []

    def add_node(val, x, y, depth):
        if depth > 3:
            return
        shapes.append(ProceduralShape(
            shape="sphere",
            position=[x, y, 0],
            scale=[0.5, 0.5, 0.5],
            color="#0F9ED5",
            label=str(val),
        ))
        spread = 2.0 / (depth + 1)
        if depth < 3:
            lx, rx = x - spread, x + spread
            add_node(val * 2, lx, y - 1.5, depth + 1)
            add_node(val * 2 + 1, rx, y - 1.5, depth + 1)
            for cx in [lx, rx]:
                shapes.append(ProceduralShape(
                    shape="cylinder",
                    position=[(cx + x) / 2, y - 0.75, 0],
                    scale=[0.04, 1.4, 0.04],
                    color="#888888",
                ))

    add_node(1, 0, 3, 0)
    return shapes


def _linked_list(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Generates a horizontal linked list.
    Nodes are spheres, connectors are short cylinders between them.
    """
    shapes = []
    comps = concept.components[:8] or ["head", "node_1", "node_2", "tail"]
    spacing = 2.2
    for i, comp in enumerate(comps):
        x = i * spacing
        shapes.append(ProceduralShape(
            shape="sphere",
            position=[x, 0, 0],
            scale=[0.55, 0.55, 0.55],
            color="#0F9ED5",
            label=comp,
        ))
        if i < len(comps) - 1:
            shapes.append(ProceduralShape(
                shape="cylinder",
                position=[x + spacing / 2, 0, 0],
                scale=[0.04, spacing * 0.85, 0.04],
                color="#888888",
            ))
    return shapes


def _stack(concept: ConceptResponse) -> list[ProceduralShape]:
    """Generates a vertical stack of boxes."""
    shapes = []
    comps = concept.components[:6] or ["bottom", "...", "top"]
    for i, comp in enumerate(comps):
        shapes.append(ProceduralShape(
            shape="box",
            position=[0, i * 1.1, 0],
            scale=[1.2, 0.9, 1.2],
            color="#156082" if i == len(comps) - 1 else "#0F9ED5",
            label=comp,
        ))
    return shapes


def _queue(concept: ConceptResponse) -> list[ProceduralShape]:
    """Generates a horizontal queue of boxes (enqueue → dequeue)."""
    shapes = []
    comps = concept.components[:6] or ["front", "...", "rear"]
    for i, comp in enumerate(comps):
        shapes.append(ProceduralShape(
            shape="box",
            position=[i * 1.6, 0, 0],
            scale=[1.2, 0.9, 1.2],
            color="#E97132" if i == 0 else "#0F9ED5",
            label=comp,
        ))
    return shapes


def _graph(concept: ConceptResponse) -> list[ProceduralShape]:
    """Generates a simple circular graph with N nodes and edges connecting them."""
    shapes = []
    comps = concept.components[:7] or [f"v{i}" for i in range(5)]
    n = len(comps)
    radius = 2.5
    positions = []
    for i, comp in enumerate(comps):
        angle = (2 * math.pi / n) * i
        x, z = radius * math.cos(angle), radius * math.sin(angle)
        positions.append((x, z))
        shapes.append(ProceduralShape(
            shape="sphere",
            position=[x, 0, z],
            scale=[0.5, 0.5, 0.5],
            color="#0F9ED5",
            label=comp,
        ))
    # Connect adjacent nodes
    for i in range(n):
        x1, z1 = positions[i]
        x2, z2 = positions[(i + 1) % n]
        shapes.append(ProceduralShape(
            shape="cylinder",
            position=[(x1 + x2) / 2, 0, (z1 + z2) / 2],
            scale=[0.04, math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2) * 0.95, 0.04],
            color="#888888",
        ))
    return shapes


def _hash_table(concept: ConceptResponse) -> list[ProceduralShape]:
    """Generates a visual hash table: bucket boxes in a column with key labels."""
    shapes = []
    buckets = concept.components[:6] or [f"bucket_{i}" for i in range(6)]
    for i, b in enumerate(buckets):
        shapes.append(ProceduralShape(
            shape="box",
            position=[0, -i * 1.2, 0],
            scale=[2.0, 0.9, 0.5],
            color="#156082",
            label=b,
        ))
    return shapes


def _molecule(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Arranges components radially around a central hub sphere.
    Good for chemical compounds, solar system analogies, network hubs.
    """
    shapes = []
    comps = concept.components[:6] or ["A", "B", "C"]
    colors = ["#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6", "#1ABC9C"]
    shapes.append(ProceduralShape(
        shape="sphere",
        position=[0, 0, 0],
        scale=[0.7, 0.7, 0.7],
        color=colors[0],
        label=comps[0],
    ))
    for i, comp in enumerate(comps[1:], 1):
        angle = (2 * math.pi / len(comps[1:])) * (i - 1)
        x, z = 2.0 * math.cos(angle), 2.0 * math.sin(angle)
        shapes.append(ProceduralShape(
            shape="sphere",
            position=[x, 0, z],
            scale=[0.5, 0.5, 0.5],
            color=colors[i % len(colors)],
            label=comp,
        ))
        shapes.append(ProceduralShape(
            shape="cylinder",
            position=[x / 2, 0, z / 2],
            scale=[0.06, 1.8, 0.06],
            color="#BBBBBB",
        ))
    return shapes


def _atom(concept: ConceptResponse) -> list[ProceduralShape]:
    """Nucleus sphere with electron orbit rings (cylinders as rings, flattened)."""
    shapes = []
    # Nucleus
    shapes.append(ProceduralShape(
        shape="sphere",
        position=[0, 0, 0],
        scale=[0.6, 0.6, 0.6],
        color="#E74C3C",
        label="nucleus",
    ))
    # Electron shells (3 orbital rings)
    for i in range(1, 4):
        r = i * 1.2
        shapes.append(ProceduralShape(
            shape="cylinder",
            position=[0, 0, 0],
            scale=[r * 2, 0.03, r * 2],
            color="#3498DB",
        ))
        # Electron on ring
        shapes.append(ProceduralShape(
            shape="sphere",
            position=[r, 0, 0],
            scale=[0.2, 0.2, 0.2],
            color="#F39C12",
            label=f"e{i}",
        ))
    return shapes


def _solar_system(concept: ConceptResponse) -> list[ProceduralShape]:
    """Sun at centre, planets orbiting radially."""
    shapes = []
    bodies = concept.components[:8] or ["sun", "mercury", "venus", "earth", "mars"]
    shapes.append(ProceduralShape(
        shape="sphere",
        position=[0, 0, 0],
        scale=[1.0, 1.0, 1.0],
        color="#F39C12",
        label=bodies[0],
    ))
    colors = ["#888888", "#E8C36A", "#3498DB", "#E74C3C", "#C67C3B", "#D2AA70"]
    for i, body in enumerate(bodies[1:], 1):
        r = i * 1.8
        shapes.append(ProceduralShape(
            shape="sphere",
            position=[r, 0, 0],
            scale=[0.35, 0.35, 0.35],
            color=colors[(i - 1) % len(colors)],
            label=body,
        ))
        # Orbit ring
        shapes.append(ProceduralShape(
            shape="cylinder",
            position=[0, 0, 0],
            scale=[r * 2, 0.02, r * 2],
            color="#555555",
        ))
    return shapes


def _generic(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Fallback: simple horizontal row of equal-size spheres, each labelled.
    Used when no specific rule matches or concept.components is empty.
    """
    comps = concept.components[:8] or ["component_1", "component_2", "component_3"]
    return [
        ProceduralShape(
            shape="sphere",
            position=[i * 1.8 - len(comps) * 0.9, 0, 0],
            scale=[0.6, 0.6, 0.6],
            color="#156082",
            label=c,
        )
        for i, c in enumerate(comps)
    ]


# ── RULES dict ─────────────────────────────────────────────────────────────────
# Keys: concept query (snake_case) OR concept.type
# Add new entries here — no changes needed in fallback_engine.py.

RULES: dict = {
    # Algorithmic / data structures
    "binary_tree": _binary_tree,
    "binary_search_tree": _binary_tree,
    "bst": _binary_tree,
    "avl_tree": _binary_tree,       # TODO: differentiate by colour/shape
    "red_black_tree": _binary_tree,
    "heap": _binary_tree,
    "linked_list": _linked_list,
    "doubly_linked_list": _linked_list,
    "stack": _stack,
    "queue": _queue,
    "deque": _queue,
    "graph": _graph,
    "hash_table": _hash_table,
    "hash_map": _hash_table,
    # Physical / scientific
    "molecule": _molecule,
    "atom": _atom,
    "solar_system": _solar_system,
    # Type-level fallbacks (concept.type as key)
    "algorithmic": _binary_tree,
    "physical": _molecule,
    "biological": _molecule,
}