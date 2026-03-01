"""
procedural_gen.py — Fallback Layer 2
Owner: Ashwin

Handles PHYSICAL and ALGORITHMIC concepts only.
Generates geometry using rule-based primitives (spheres, cylinders, boxes, cones).
Returns a FallbackResponse with a geometry list that Three.js can render.
COMPLETELY SEPARATE from conceptual_viz.py (Ashutosh's Layer 3).

The RULES dict maps concept names → specialized generator functions.
Add new entries here to support more concept types without touching the engine.

Colour palette used across all generators:
  #0F9ED5  — primary blue       (default nodes)
  #156082  — deep navy          (root / important nodes)
  #E97132  — orange             (highlighted / top nodes)
  #E74C3C  — red                (warnings, red-black tree red nodes)
  #2ECC71  — green              (positive / matched)
  #F39C12  — amber              (medium confidence)
  #9B59B6  — purple             (special nodes)
  #1ABC9C  — teal               (biological)
  #888888  — grey               (edges / connectors)
  #BBBBBB  — light grey         (secondary connectors)
"""

import math
from app.models.schemas import ConceptResponse, FallbackResponse, ProceduralShape


# ── Colour helpers ─────────────────────────────────────────────────────────────

# Depth-based colour gradient for trees: root=navy → leaves=light blue
DEPTH_COLORS = ["#156082", "#0F9ED5", "#3498DB", "#85C1E9", "#AED6F1"]

# Standard palette for multi-component concepts
PALETTE = ["#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6",
           "#1ABC9C", "#E97132", "#0F9ED5", "#156082", "#85C1E9"]


def generate(concept: ConceptResponse) -> FallbackResponse:
    """
    Entry point called by fallback_engine.py when strategy includes 'procedural'.
    Normalises the concept query to a snake_case key and looks it up in RULES.
    Falls back to concept.type as key, then _generic() if nothing matches.
    Never returns None — always produces at least a generic arrangement of shapes.
    """
    key = concept.query.lower().replace(" ", "_")
    rule_fn = RULES.get(key) or RULES.get(concept.type)
    shapes = rule_fn(concept) if rule_fn else _generic(concept)

    # Edge case: if somehow shapes is empty, fall back to generic
    if not shapes:
        shapes = _generic(concept)

    return FallbackResponse(
        layer_used=2,
        layer_name="Procedural Geometry Generation",
        result_type="procedural",
        model=None,
        geometry=shapes,
        explanation=(
            f'No matching 3D model for "{concept.query}". '
            f'Generated a structural approximation using geometric primitives. '
            f'Components rendered: {[s.label for s in shapes if s.label]}.'
        ),
    )


def _depth_color(depth: int) -> str:
    """Returns a colour that gets lighter as depth increases."""
    return DEPTH_COLORS[min(depth, len(DEPTH_COLORS) - 1)]


def _node_size(depth: int) -> float:
    """Root nodes are bigger; leaf nodes are smaller."""
    return max(0.3, 0.6 - depth * 0.08)


def _edge(x1, y1, z1, x2, y2, z2, color="#888888", thickness=0.04) -> ProceduralShape:
    """
    Helper: creates a cylinder connecting two 3D points.
    Automatically computes midpoint and length.
    """
    mx, my, mz = (x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2
    length = math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
    return ProceduralShape(
        shape="cylinder",
        position=[mx, my, mz],
        scale=[thickness, length * 0.95, thickness],
        color=color,
    )


# ── Tree generators ────────────────────────────────────────────────────────────

def _binary_tree(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Full BST up to depth 3.
    - Node size decreases with depth
    - Node colour gets lighter with depth
    - Edges are grey cylinders
    - Labels use component names if provided, else node numbers
    """
    shapes = []
    labels = concept.components[:15] if concept.components else []

    def add_node(val, x, y, depth):
        if depth > 3:
            return
        size = _node_size(depth)
        color = _depth_color(depth)
        label = labels[val - 1] if val - 1 < len(labels) else str(val)
        shapes.append(ProceduralShape(
            shape="sphere",
            position=[x, y, 0],
            scale=[size, size, size],
            color=color,
            label=label,
        ))
        if depth < 3:
            spread = 2.2 / (depth + 1)
            lx, rx = x - spread, x + spread
            ny = y - 1.6
            # Left child
            add_node(val * 2, lx, ny, depth + 1)
            shapes.append(_edge(x, y, 0, lx, ny, 0))
            # Right child
            add_node(val * 2 + 1, rx, ny, depth + 1)
            shapes.append(_edge(x, y, 0, rx, ny, 0))

    add_node(1, 0, 3, 0)
    return shapes


def _avl_tree(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    AVL tree — same structure as BST but nodes show balance factors.
    Balanced nodes = green, unbalanced = amber.
    """
    shapes = []
    balance_factors = [0, 1, -1, 0, 1, 0, -1, 0]  # simulated BF values

    def add_node(val, x, y, depth):
        if depth > 3:
            return
        bf = balance_factors[(val - 1) % len(balance_factors)]
        color = "#2ECC71" if bf == 0 else "#F39C12" if abs(bf) == 1 else "#E74C3C"
        size = _node_size(depth)
        label = f"BF:{bf}"
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, y, 0],
            scale=[size, size, size], color=color, label=label,
        ))
        if depth < 3:
            spread = 2.2 / (depth + 1)
            lx, rx = x - spread, x + spread
            ny = y - 1.6
            add_node(val * 2, lx, ny, depth + 1)
            shapes.append(_edge(x, y, 0, lx, ny, 0, color="#2ECC71"))
            add_node(val * 2 + 1, rx, ny, depth + 1)
            shapes.append(_edge(x, y, 0, rx, ny, 0, color="#2ECC71"))

    add_node(1, 0, 3, 0)
    return shapes


def _red_black_tree(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Red-Black tree — nodes alternate red (#E74C3C) and black (#2C3E50).
    Root is always black. Demonstrates RB tree colouring rules visually.
    """
    shapes = []
    # RB pattern: root=black, children alternate
    rb_colors = ["#2C3E50", "#E74C3C", "#E74C3C", "#2C3E50",
                 "#2C3E50", "#2C3E50", "#2C3E50", "#E74C3C",
                 "#E74C3C", "#E74C3C", "#E74C3C", "#E74C3C",
                 "#E74C3C", "#E74C3C", "#E74C3C"]

    def add_node(val, x, y, depth):
        if depth > 3:
            return
        color = rb_colors[(val - 1) % len(rb_colors)]
        label = "R" if color == "#E74C3C" else "B"
        size = _node_size(depth)
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, y, 0],
            scale=[size, size, size], color=color, label=label,
        ))
        if depth < 3:
            spread = 2.2 / (depth + 1)
            lx, rx = x - spread, x + spread
            ny = y - 1.6
            add_node(val * 2, lx, ny, depth + 1)
            shapes.append(_edge(x, y, 0, lx, ny, 0, color="#555555"))
            add_node(val * 2 + 1, rx, ny, depth + 1)
            shapes.append(_edge(x, y, 0, rx, ny, 0, color="#555555"))

    add_node(1, 0, 3, 0)
    return shapes


def _min_heap(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Min-heap — complete binary tree where parent is always smaller.
    Root (minimum) is highlighted in orange. Values increase downward.
    """
    shapes = []
    values = [1, 3, 2, 7, 5, 6, 4, 9, 8, 10, 11, 12, 13, 14, 15]

    def add_node(idx, x, y, depth):
        if depth > 3 or idx >= len(values):
            return
        val = values[idx]
        color = "#E97132" if idx == 0 else _depth_color(depth)
        size = _node_size(depth)
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, y, 0],
            scale=[size, size, size], color=color, label=str(val),
        ))
        if depth < 3:
            spread = 2.2 / (depth + 1)
            lx, rx = x - spread, x + spread
            ny = y - 1.6
            left_idx, right_idx = 2 * idx + 1, 2 * idx + 2
            if left_idx < len(values):
                add_node(left_idx, lx, ny, depth + 1)
                shapes.append(_edge(x, y, 0, lx, ny, 0))
            if right_idx < len(values):
                add_node(right_idx, rx, ny, depth + 1)
                shapes.append(_edge(x, y, 0, rx, ny, 0))

    add_node(0, 0, 3, 0)
    return shapes


def _max_heap(concept: ConceptResponse) -> list[ProceduralShape]:
    """Max-heap — root is the maximum value, highlighted in red."""
    shapes = []
    values = [15, 13, 14, 9, 10, 11, 12, 5, 6, 7, 8, 3, 4, 1, 2]

    def add_node(idx, x, y, depth):
        if depth > 3 or idx >= len(values):
            return
        val = values[idx]
        color = "#E74C3C" if idx == 0 else _depth_color(depth)
        size = _node_size(depth)
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, y, 0],
            scale=[size, size, size], color=color, label=str(val),
        ))
        if depth < 3:
            spread = 2.2 / (depth + 1)
            lx, rx = x - spread, x + spread
            ny = y - 1.6
            left_idx, right_idx = 2 * idx + 1, 2 * idx + 2
            if left_idx < len(values):
                add_node(left_idx, lx, ny, depth + 1)
                shapes.append(_edge(x, y, 0, lx, ny, 0))
            if right_idx < len(values):
                add_node(right_idx, rx, ny, depth + 1)
                shapes.append(_edge(x, y, 0, rx, ny, 0))

    add_node(0, 0, 3, 0)
    return shapes


# ── List / linear structures ───────────────────────────────────────────────────

def _linked_list(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Singly linked list — nodes are spheres, arrows are cylinders.
    HEAD is highlighted orange, TAIL is highlighted navy.
    Pointer direction shown by colour gradient left → right.
    """
    shapes = []
    comps = concept.components[:8] or ["HEAD", "node_1", "node_2", "node_3", "TAIL"]
    spacing = 2.4
    n = len(comps)

    for i, comp in enumerate(comps):
        # Colour: head=orange, tail=navy, middle=blue gradient
        if i == 0:
            color = "#E97132"
        elif i == n - 1:
            color = "#156082"
        else:
            t = i / max(n - 1, 1)
            color = "#0F9ED5" if t < 0.5 else "#3498DB"

        x = i * spacing - (n - 1) * spacing / 2  # centre the list
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, 0, 0],
            scale=[0.55, 0.55, 0.55], color=color, label=comp,
        ))
        # Arrow/pointer to next node
        if i < n - 1:
            nx = (i + 1) * spacing - (n - 1) * spacing / 2
            shapes.append(_edge(x, 0, 0, nx, 0, 0, color="#AAAAAA", thickness=0.05))
            # Arrowhead cone at midpoint
            shapes.append(ProceduralShape(
                shape="cone",
                position=[x + spacing * 0.72, 0, 0],
                scale=[0.12, 0.25, 0.12],
                color="#AAAAAA",
            ))
    return shapes


def _doubly_linked_list(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Doubly linked list — two sets of cylinders for forward and backward pointers.
    Forward pointers are blue, backward pointers are orange.
    """
    shapes = []
    comps = concept.components[:6] or ["HEAD", "node_1", "node_2", "node_3", "TAIL"]
    spacing = 2.6
    n = len(comps)

    for i, comp in enumerate(comps):
        color = "#E97132" if i == 0 else "#156082" if i == n - 1 else "#0F9ED5"
        x = i * spacing - (n - 1) * spacing / 2
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, 0, 0],
            scale=[0.55, 0.55, 0.55], color=color, label=comp,
        ))
        if i < n - 1:
            nx = (i + 1) * spacing - (n - 1) * spacing / 2
            # Forward pointer (slightly above centre)
            shapes.append(_edge(x, 0.15, 0, nx, 0.15, 0, color="#0F9ED5", thickness=0.04))
            # Backward pointer (slightly below centre)
            shapes.append(_edge(nx, -0.15, 0, x, -0.15, 0, color="#E97132", thickness=0.04))
    return shapes


def _circular_linked_list(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Circular linked list — nodes arranged in a circle, last node points back to head.
    """
    shapes = []
    comps = concept.components[:7] or ["HEAD", "node_1", "node_2", "node_3", "node_4"]
    n = len(comps)
    radius = 2.5

    positions = []
    for i, comp in enumerate(comps):
        angle = (2 * math.pi / n) * i - math.pi / 2  # start at top
        x, z = radius * math.cos(angle), radius * math.sin(angle)
        positions.append((x, z))
        color = "#E97132" if i == 0 else "#0F9ED5"
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, 0, z],
            scale=[0.55, 0.55, 0.55], color=color, label=comp,
        ))

    # Connect all nodes including last → first
    for i in range(n):
        x1, z1 = positions[i]
        x2, z2 = positions[(i + 1) % n]
        shapes.append(_edge(x1, 0, z1, x2, 0, z2, color="#888888"))

    return shapes


def _stack(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Stack — vertical tower of boxes.
    TOP is highlighted (most recently pushed).
    Shows PUSH direction with upward arrow.
    """
    shapes = []
    comps = concept.components[:6] or ["bottom", "item_2", "item_3", "item_4", "TOP"]
    n = len(comps)

    for i, comp in enumerate(comps):
        # Bottom=dark, top=bright orange
        t = i / max(n - 1, 1)
        r = int(0x15 + t * (0xE9 - 0x15))
        g = int(0x60 + t * (0x71 - 0x60))
        b = int(0x82 + t * (0x32 - 0x82))
        color = f"#{r:02X}{g:02X}{b:02X}"
        if i == n - 1:
            color = "#E97132"  # TOP is always orange

        shapes.append(ProceduralShape(
            shape="box", position=[0, i * 1.1, 0],
            scale=[1.8, 0.95, 1.0], color=color, label=comp,
        ))

    # PUSH arrow above stack
    top_y = (n - 1) * 1.1
    shapes.append(ProceduralShape(
        shape="cylinder", position=[0, top_y + 0.9, 0],
        scale=[0.05, 0.8, 0.05], color="#2ECC71",
    ))
    shapes.append(ProceduralShape(
        shape="cone", position=[0, top_y + 1.4, 0],
        scale=[0.15, 0.3, 0.15], color="#2ECC71", label="PUSH",
    ))
    return shapes


def _queue(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Queue — horizontal row of boxes.
    FRONT (dequeue end) = red, REAR (enqueue end) = green.
    Arrows show direction of flow.
    """
    shapes = []
    comps = concept.components[:6] or ["FRONT", "item_2", "item_3", "item_4", "REAR"]
    n = len(comps)
    spacing = 2.0

    for i, comp in enumerate(comps):
        if i == 0:
            color = "#E74C3C"    # FRONT = red (dequeue here)
        elif i == n - 1:
            color = "#2ECC71"    # REAR = green (enqueue here)
        else:
            color = "#0F9ED5"

        x = i * spacing - (n - 1) * spacing / 2
        shapes.append(ProceduralShape(
            shape="box", position=[x, 0, 0],
            scale=[1.6, 0.9, 1.0], color=color, label=comp,
        ))

    # Dequeue arrow on left
    leftmost_x = -(n - 1) * spacing / 2
    shapes.append(_edge(leftmost_x - 0.8, 0, 0, leftmost_x - 1.6, 0, 0,
                        color="#E74C3C", thickness=0.06))
    shapes.append(ProceduralShape(
        shape="cone", position=[leftmost_x - 1.7, 0, 0],
        scale=[0.15, 0.3, 0.15], color="#E74C3C", label="DEQ",
    ))

    # Enqueue arrow on right
    rightmost_x = (n - 1) * spacing / 2
    shapes.append(_edge(rightmost_x + 1.6, 0, 0, rightmost_x + 0.8, 0, 0,
                        color="#2ECC71", thickness=0.06))
    shapes.append(ProceduralShape(
        shape="cone", position=[rightmost_x + 0.7, 0, 0],
        scale=[0.15, 0.3, 0.15], color="#2ECC71", label="ENQ",
    ))
    return shapes


# ── Graph structures ───────────────────────────────────────────────────────────

def _graph(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Undirected graph — nodes in a circle with edges connecting them.
    Uses a predefined edge set for a realistic graph (not just a ring).
    Node colours vary by position for visual distinction.
    """
    shapes = []
    comps = concept.components[:8] or [f"V{i}" for i in range(6)]
    n = len(comps)
    radius = 2.8
    positions = []

    for i, comp in enumerate(comps):
        angle = (2 * math.pi / n) * i - math.pi / 2
        x, z = radius * math.cos(angle), radius * math.sin(angle)
        positions.append((x, z))
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, 0, z],
            scale=[0.55, 0.55, 0.55],
            color=PALETTE[i % len(PALETTE)], label=comp,
        ))

    # Edges: ring + a few cross edges for realism
    edges = [(i, (i + 1) % n) for i in range(n)]
    if n >= 4:
        edges += [(0, 2), (1, 3)]
    if n >= 6:
        edges += [(0, 3), (2, 5)]

    seen = set()
    for a, b in edges:
        key = (min(a, b), max(a, b))
        if key in seen:
            continue
        seen.add(key)
        x1, z1 = positions[a]
        x2, z2 = positions[b]
        shapes.append(_edge(x1, 0, z1, x2, 0, z2, color="#888888", thickness=0.04))

    return shapes


def _directed_graph(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Directed graph (digraph) — same as graph but with cone arrowheads on edges.
    """
    shapes = []
    comps = concept.components[:6] or [f"V{i}" for i in range(5)]
    n = len(comps)
    radius = 2.5
    positions = []

    for i, comp in enumerate(comps):
        angle = (2 * math.pi / n) * i - math.pi / 2
        x, z = radius * math.cos(angle), radius * math.sin(angle)
        positions.append((x, z))
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, 0, z],
            scale=[0.55, 0.55, 0.55],
            color=PALETTE[i % len(PALETTE)], label=comp,
        ))

    # Directed edges with arrowheads
    edges = [(i, (i + 1) % n) for i in range(n)]
    if n >= 4:
        edges.append((0, 2))

    for a, b in edges:
        x1, z1 = positions[a]
        x2, z2 = positions[b]
        shapes.append(_edge(x1, 0, z1, x2, 0, z2, color="#0F9ED5", thickness=0.04))
        # Arrowhead near target node
        mx = x1 * 0.25 + x2 * 0.75
        mz = z1 * 0.25 + z2 * 0.75
        shapes.append(ProceduralShape(
            shape="cone", position=[mx, 0, mz],
            scale=[0.12, 0.25, 0.12], color="#0F9ED5",
        ))

    return shapes


def _hash_table(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Hash table — column of bucket boxes with index labels.
    Some buckets have 'chained' nodes beside them (collision handling).
    """
    shapes = []
    buckets = concept.components[:8] or [f"bucket_{i}" for i in range(6)]
    n = len(buckets)

    for i, b in enumerate(buckets):
        y = -i * 1.3
        # Index label box (dark)
        shapes.append(ProceduralShape(
            shape="box", position=[-1.5, y, 0],
            scale=[0.8, 1.0, 0.5], color="#2C3E50", label=str(i),
        ))
        # Bucket box
        shapes.append(ProceduralShape(
            shape="box", position=[0.2, y, 0],
            scale=[2.0, 1.0, 0.5], color="#156082", label=b,
        ))
        # Connector between index and bucket
        shapes.append(_edge(-1.1, y, 0, -0.8, y, 0, color="#AAAAAA", thickness=0.04))

        # Simulate collision chain on every 3rd bucket
        if i % 3 == 1:
            shapes.append(ProceduralShape(
                shape="sphere", position=[2.2, y, 0],
                scale=[0.35, 0.35, 0.35], color="#E97132", label="chain",
            ))
            shapes.append(_edge(1.2, y, 0, 1.85, y, 0, color="#E97132", thickness=0.04))

    return shapes


# ── Physical / scientific ──────────────────────────────────────────────────────

def _molecule(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Molecule — central atom surrounded by bonded atoms in 3D.
    Uses two orbital layers for more complex molecules.
    Bond thickness varies by bond type (single/double).
    """
    shapes = []
    comps = concept.components[:8] or ["C", "H", "H", "H", "H", "O"]
    n = len(comps)

    # Central atom (larger)
    shapes.append(ProceduralShape(
        shape="sphere", position=[0, 0, 0],
        scale=[0.8, 0.8, 0.8], color="#E74C3C", label=comps[0],
    ))

    inner = comps[1:5]
    outer = comps[5:]

    # Inner ring atoms
    for i, comp in enumerate(inner):
        angle = (2 * math.pi / len(inner)) * i
        x, z = 2.0 * math.cos(angle), 2.0 * math.sin(angle)
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, 0, z],
            scale=[0.5, 0.5, 0.5], color=PALETTE[(i + 1) % len(PALETTE)], label=comp,
        ))
        shapes.append(_edge(0, 0, 0, x, 0, z, color="#CCCCCC", thickness=0.07))

    # Outer ring atoms (slightly elevated for 3D feel)
    for i, comp in enumerate(outer):
        angle = (2 * math.pi / max(len(outer), 1)) * i + math.pi / len(outer)
        x, z = 3.2 * math.cos(angle), 3.2 * math.sin(angle)
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, 0.8, z],
            scale=[0.4, 0.4, 0.4], color=PALETTE[(i + 5) % len(PALETTE)], label=comp,
        ))
        # Bond to nearest inner atom
        inner_idx = i % len(inner) if inner else 0
        if inner:
            inner_angle = (2 * math.pi / len(inner)) * inner_idx
            ix, iz = 2.0 * math.cos(inner_angle), 2.0 * math.sin(inner_angle)
            shapes.append(_edge(ix, 0, iz, x, 0.8, z, color="#BBBBBB", thickness=0.04))

    return shapes


def _atom(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Atom — nucleus with protons/neutrons, surrounded by electron shells.
    Shell 1 = 2 electrons, Shell 2 = 8 electrons (simplified Bohr model).
    """
    shapes = []

    # Nucleus (protons = red, neutrons = blue, clustered together)
    nucleus_parts = concept.components[:4] or ["proton", "proton", "neutron", "neutron"]
    offsets = [[0.1, 0, 0], [-0.1, 0, 0], [0, 0.1, 0], [0, -0.1, 0]]
    for i, part in enumerate(nucleus_parts[:4]):
        off = offsets[i]
        color = "#E74C3C" if "proton" in part.lower() else "#3498DB"
        shapes.append(ProceduralShape(
            shape="sphere", position=off,
            scale=[0.25, 0.25, 0.25], color=color, label=part[:1].upper(),
        ))

    # Electron shells
    shell_configs = [(1.8, 2, "#F39C12"), (3.2, 4, "#2ECC71"), (4.6, 2, "#9B59B6")]
    for radius, count, color in shell_configs:
        # Orbit ring
        shapes.append(ProceduralShape(
            shape="cylinder", position=[0, 0, 0],
            scale=[radius * 2, 0.02, radius * 2], color="#555555",
        ))
        # Electrons on ring
        for j in range(count):
            angle = (2 * math.pi / count) * j
            x, z = radius * math.cos(angle), radius * math.sin(angle)
            shapes.append(ProceduralShape(
                shape="sphere", position=[x, 0, z],
                scale=[0.18, 0.18, 0.18], color=color, label="e⁻",
            ))

    return shapes


def _dna(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    DNA double helix — two intertwined strands of spheres connected by rungs.
    Strand 1 = blue, Strand 2 = red, base pair rungs = grey cylinders.
    """
    shapes = []
    steps = 12      # number of base pairs
    height_step = 0.6
    radius = 1.0
    twist = math.pi / 4  # rotation per step

    base_pairs = concept.components[:steps] or \
        ["A-T", "G-C", "T-A", "C-G", "A-T", "G-C",
         "T-A", "C-G", "A-T", "G-C", "T-A", "C-G"]

    for i in range(steps):
        y = i * height_step - (steps * height_step) / 2
        angle = i * twist

        # Strand 1 (blue)
        x1, z1 = radius * math.cos(angle), radius * math.sin(angle)
        shapes.append(ProceduralShape(
            shape="sphere", position=[x1, y, z1],
            scale=[0.25, 0.25, 0.25], color="#3498DB",
            label=base_pairs[i].split("-")[0] if i < len(base_pairs) and "-" in base_pairs[i] else (base_pairs[i] if i < len(base_pairs) else ""),
        ))

        # Strand 2 (red, opposite side)
        x2, z2 = radius * math.cos(angle + math.pi), radius * math.sin(angle + math.pi)
        shapes.append(ProceduralShape(
            shape="sphere", position=[x2, y, z2],
            scale=[0.25, 0.25, 0.25], color="#E74C3C",
            label=base_pairs[i].split("-")[1] if i < len(base_pairs) and "-" in base_pairs[i] else "",
        ))

        # Base pair rung
        shapes.append(_edge(x1, y, z1, x2, y, z2, color="#888888", thickness=0.04))

        # Backbone connections (strand 1)
        if i > 0:
            prev_angle = (i - 1) * twist
            px1 = radius * math.cos(prev_angle)
            pz1 = radius * math.sin(prev_angle)
            py = (i - 1) * height_step - (steps * height_step) / 2
            shapes.append(_edge(px1, py, pz1, x1, y, z1, color="#85C1E9", thickness=0.06))

            # Backbone connections (strand 2)
            px2 = radius * math.cos(prev_angle + math.pi)
            pz2 = radius * math.sin(prev_angle + math.pi)
            shapes.append(_edge(px2, py, pz2, x2, y, z2, color="#F1948A", thickness=0.06))

    return shapes


def _solar_system(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Solar system — sun at centre with planets at correct relative positions.
    Planet sizes vary realistically. Orbit rings shown as flat cylinders.
    """
    shapes = []
    planet_data = [
        ("sun",     0,    1.2,  "#F39C12"),
        ("mercury", 2.0,  0.18, "#888888"),
        ("venus",   3.0,  0.28, "#E8C36A"),
        ("earth",   4.2,  0.30, "#3498DB"),
        ("mars",    5.5,  0.22, "#E74C3C"),
        ("jupiter", 7.5,  0.60, "#C67C3B"),
        ("saturn",  9.5,  0.52, "#D2AA70"),
        ("uranus",  11.0, 0.38, "#85C1E9"),
        ("neptune", 12.5, 0.35, "#2980B9"),
    ]

    # Override with concept components if provided
    bodies = concept.components[:9] if concept.components else []
    for i, (name, r, size, color) in enumerate(planet_data):
        label = bodies[i] if i < len(bodies) else name
        shapes.append(ProceduralShape(
            shape="sphere", position=[r, 0, 0],
            scale=[size, size, size], color=color, label=label,
        ))
        if r > 0:
            # Orbit ring
            shapes.append(ProceduralShape(
                shape="cylinder", position=[0, 0, 0],
                scale=[r * 2, 0.015, r * 2], color="#333333",
            ))

    # Saturn's rings (extra flat cylinders)
    shapes.append(ProceduralShape(
        shape="cylinder", position=[9.5, 0, 0],
        scale=[1.6, 0.02, 1.6], color="#C8A96E",
    ))

    return shapes


def _neural_network(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Neural network — layered architecture with input, hidden, and output layers.
    Nodes are spheres, connections are thin cylinders.
    Input=blue, Hidden=orange, Output=green.
    """
    shapes = []
    # [input_nodes, hidden1, hidden2, output_nodes]
    layer_sizes = [4, 5, 5, 3]
    layer_colors = ["#3498DB", "#E97132", "#E97132", "#2ECC71"]
    layer_labels = ["input", "hidden", "hidden", "output"]
    x_positions = [-4.5, -1.5, 1.5, 4.5]
    node_positions = {}  # (layer, node_idx) → (x, y)

    for l, (size, color, lx) in enumerate(zip(layer_sizes, layer_colors, x_positions)):
        for n in range(size):
            y = (n - (size - 1) / 2) * 1.4
            node_positions[(l, n)] = (lx, y)
            label = layer_labels[l] if n == size // 2 else ""
            shapes.append(ProceduralShape(
                shape="sphere", position=[lx, y, 0],
                scale=[0.35, 0.35, 0.35], color=color, label=label,
            ))

    # Connections between adjacent layers
    for l in range(len(layer_sizes) - 1):
        for n1 in range(layer_sizes[l]):
            for n2 in range(layer_sizes[l + 1]):
                x1, y1 = node_positions[(l, n1)]
                x2, y2 = node_positions[(l + 1, n2)]
                shapes.append(_edge(x1, y1, 0, x2, y2, 0,
                                    color="#555555", thickness=0.02))

    return shapes


def _matrix(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Matrix / 2D grid — NxM grid of boxes.
    Diagonal elements highlighted (identity matrix pattern).
    """
    shapes = []
    rows, cols = 4, 4
    spacing = 1.3

    for r in range(rows):
        for c in range(cols):
            x = (c - (cols - 1) / 2) * spacing
            y = ((rows - 1) / 2 - r) * spacing
            is_diag = (r == c)
            color = "#E97132" if is_diag else "#156082"
            label = "1" if is_diag else "0"
            shapes.append(ProceduralShape(
                shape="box", position=[x, y, 0],
                scale=[1.1, 1.1, 0.3], color=color, label=label,
            ))

    return shapes


def _sorting_algorithm(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Sorting algorithm visualisation — bars of different heights representing array elements.
    Unsorted = blue, being compared = orange, sorted = green.
    Simulates a mid-sort snapshot.
    """
    shapes = []
    values = [7, 2, 9, 4, 6, 1, 8, 3, 5]
    n = len(values)
    # Simulate: first 3 are sorted, index 3-4 being compared, rest unsorted
    for i, val in enumerate(values):
        x = (i - (n - 1) / 2) * 1.4
        height = val * 0.4
        if i < 3:
            color = "#2ECC71"   # sorted
        elif i in [3, 4]:
            color = "#E97132"   # being compared
        else:
            color = "#0F9ED5"   # unsorted

        shapes.append(ProceduralShape(
            shape="box", position=[x, height / 2, 0],
            scale=[1.0, height, 0.8], color=color, label=str(val),
        ))

    return shapes


def _inclined_plane(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Inclined plane — tilted ramp (box) with a sphere on it.
    Angle shown by the ramp geometry. Force arrows as cylinders.
    """
    shapes = []
    angle_deg = 40  # default 40 degrees as user mentioned
    angle_rad = math.radians(angle_deg)

    # The ramp (a flat box rotated conceptually by positioning)
    ramp_len = 5.0
    shapes.append(ProceduralShape(
        shape="box",
        position=[0, -0.5, 0],
        scale=[ramp_len, 0.2, 1.5],
        color="#8D6E63",
        label=f"ramp ({angle_deg}°)",
    ))

    # Object on the plane
    obj_x = ramp_len * 0.25 * math.cos(angle_rad)
    obj_y = ramp_len * 0.25 * math.sin(angle_rad)
    shapes.append(ProceduralShape(
        shape="sphere",
        position=[obj_x - 1.0, obj_y + 0.3, 0],
        scale=[0.4, 0.4, 0.4],
        color="#E97132",
        label="object",
    ))

    # Gravity vector (downward arrow)
    shapes.append(ProceduralShape(
        shape="cylinder", position=[obj_x - 1.0, obj_y - 0.4, 0],
        scale=[0.05, 0.8, 0.05], color="#E74C3C",
    ))
    shapes.append(ProceduralShape(
        shape="cone", position=[obj_x - 1.0, obj_y - 0.9, 0],
        scale=[0.12, 0.25, 0.12], color="#E74C3C", label="gravity",
    ))

    # Normal force vector (perpendicular to plane)
    nx = -math.sin(angle_rad) * 0.8
    ny = math.cos(angle_rad) * 0.8
    shapes.append(ProceduralShape(
        shape="cylinder", position=[obj_x - 1.0 + nx/2, obj_y + 0.3 + ny/2, 0],
        scale=[0.05, 0.8, 0.05], color="#2ECC71",
    ))
    shapes.append(ProceduralShape(
        shape="cone", position=[obj_x - 1.0 + nx, obj_y + 0.3 + ny, 0],
        scale=[0.12, 0.25, 0.12], color="#2ECC71", label="normal",
    ))

    # Friction vector (along plane, opposing motion)
    fx = math.cos(angle_rad) * 0.6
    fy = math.sin(angle_rad) * 0.6
    shapes.append(ProceduralShape(
        shape="cylinder", position=[obj_x - 1.0 + fx/2, obj_y + 0.3 + fy/2, 0],
        scale=[0.05, 0.6, 0.05], color="#9B59B6",
    ))
    shapes.append(ProceduralShape(
        shape="cone", position=[obj_x - 1.0 + fx, obj_y + 0.3 + fy, 0],
        scale=[0.12, 0.25, 0.12], color="#9B59B6", label="friction",
    ))

    return shapes


def _cpu(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    CPU architecture — core boxes surrounded by cache layers and bus connections.
    """
    shapes = []

    # CPU cores (4 cores in a 2x2 grid)
    core_positions = [(-1.0, 0.8), (1.0, 0.8), (-1.0, -0.8), (1.0, -0.8)]
    for i, (cx, cy) in enumerate(core_positions):
        shapes.append(ProceduralShape(
            shape="box", position=[cx, cy, 0],
            scale=[1.5, 1.2, 0.4], color="#156082", label=f"Core {i+1}",
        ))

    # L1 Cache around each core
    for cx, cy in core_positions:
        shapes.append(ProceduralShape(
            shape="box", position=[cx, cy, 0],
            scale=[1.8, 1.5, 0.3], color="#0F9ED5",
        ))

    # L2 Cache (shared, larger box)
    shapes.append(ProceduralShape(
        shape="box", position=[0, 0, -0.5],
        scale=[4.5, 3.5, 0.2], color="#3498DB", label="L2 Cache",
    ))

    # L3 Cache (outer ring)
    shapes.append(ProceduralShape(
        shape="box", position=[0, 0, -0.8],
        scale=[6.0, 5.0, 0.15], color="#85C1E9", label="L3 Cache",
    ))

    # Bus connections
    for cx, cy in core_positions:
        shapes.append(_edge(cx, cy, 0, 0, 0, -0.5, color="#E97132", thickness=0.05))

    # ALU and Control Unit
    shapes.append(ProceduralShape(
        shape="box", position=[-3.5, 0, 0],
        scale=[1.5, 1.0, 0.4], color="#E97132", label="ALU",
    ))
    shapes.append(ProceduralShape(
        shape="box", position=[3.5, 0, 0],
        scale=[1.5, 1.0, 0.4], color="#9B59B6", label="Control",
    ))
    shapes.append(_edge(-3.5, 0, 0, -2.25, 0, 0, color="#E97132", thickness=0.06))
    shapes.append(_edge(3.5, 0, 0, 2.25, 0, 0, color="#9B59B6", thickness=0.06))

    return shapes


def _cell(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Biological cell — cell membrane, nucleus, and organelles.
    """
    shapes = []

    # Cell membrane (large outer sphere, slightly transparent-looking via color)
    shapes.append(ProceduralShape(
        shape="sphere", position=[0, 0, 0],
        scale=[4.0, 3.5, 3.5], color="#AED6F1", label="membrane",
    ))

    # Nucleus (large central sphere)
    shapes.append(ProceduralShape(
        shape="sphere", position=[-0.5, 0.3, 0],
        scale=[1.2, 1.2, 1.2], color="#1ABC9C", label="nucleus",
    ))

    # Nucleolus inside nucleus
    shapes.append(ProceduralShape(
        shape="sphere", position=[-0.5, 0.3, 0],
        scale=[0.5, 0.5, 0.5], color="#16A085", label="nucleolus",
    ))

    # Organelles
    organelles = [
        (2.0, 0.5, "#E74C3C", "mitochon."),
        (1.5, -1.5, "#E74C3C", "mitochon."),
        (-2.0, -0.8, "#F39C12", "golgi"),
        (0.5, 2.0, "#9B59B6", "ribosome"),
        (-1.5, 1.5, "#2ECC71", "vacuole"),
        (2.0, -1.0, "#E97132", "ER"),
    ]
    comps = concept.components[1:] if len(concept.components) > 1 else []
    for i, (x, y, color, default_label) in enumerate(organelles):
        label = comps[i] if i < len(comps) else default_label
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, y, 0],
            scale=[0.45, 0.45, 0.45], color=color, label=label,
        ))

    return shapes


def _generic(concept: ConceptResponse) -> list[ProceduralShape]:
    """
    Improved generic fallback — groups components into clusters rather than a flat row.
    First component = central hub, others orbit it.
    Shows spatial_description as label context.
    """
    shapes = []
    comps = concept.components[:10] or ["component_1", "component_2", "component_3"]
    n = len(comps)

    if n == 1:
        shapes.append(ProceduralShape(
            shape="sphere", position=[0, 0, 0],
            scale=[0.8, 0.8, 0.8], color="#156082", label=comps[0],
        ))
        return shapes

    if n <= 4:
        # Simple row for small component counts
        for i, comp in enumerate(comps):
            x = (i - (n - 1) / 2) * 2.0
            shapes.append(ProceduralShape(
                shape="sphere", position=[x, 0, 0],
                scale=[0.6, 0.6, 0.6], color=PALETTE[i % len(PALETTE)], label=comp,
            ))
            if i < n - 1:
                shapes.append(_edge(x, 0, 0, x + 2.0, 0, 0, color="#888888"))
        return shapes

    # Hub-and-spoke for larger component counts
    shapes.append(ProceduralShape(
        shape="sphere", position=[0, 0, 0],
        scale=[0.8, 0.8, 0.8], color="#156082", label=comps[0],
    ))
    for i, comp in enumerate(comps[1:], 1):
        angle = (2 * math.pi / (n - 1)) * (i - 1)
        r = 2.5 if i <= 5 else 4.0
        x, z = r * math.cos(angle), r * math.sin(angle)
        shapes.append(ProceduralShape(
            shape="sphere", position=[x, 0, z],
            scale=[0.5, 0.5, 0.5], color=PALETTE[i % len(PALETTE)], label=comp,
        ))
        shapes.append(_edge(0, 0, 0, x, 0, z, color="#888888", thickness=0.04))

    return shapes


# ── RULES dict ─────────────────────────────────────────────────────────────────
# Keys: concept query (snake_case) OR concept.type
# Add new entries here — fallback_engine.py needs NO changes.

RULES: dict = {
    # ── Trees ──────────────────────────────────────────────────────────────────
    "binary_tree":          _binary_tree,
    "binary_search_tree":   _binary_tree,
    "bst":                  _binary_tree,
    "avl_tree":             _avl_tree,
    "avl":                  _avl_tree,
    "red_black_tree":       _red_black_tree,
    "red-black_tree":       _red_black_tree,
    "min_heap":             _min_heap,
    "max_heap":             _max_heap,
    "heap":                 _min_heap,
    "priority_queue":       _min_heap,

    # ── Linear structures ──────────────────────────────────────────────────────
    "linked_list":          _linked_list,
    "singly_linked_list":   _linked_list,
    "doubly_linked_list":   _doubly_linked_list,
    "circular_linked_list": _circular_linked_list,
    "stack":                _stack,
    "queue":                _queue,
    "deque":                _queue,
    "array":                _sorting_algorithm,
    "sorting":              _sorting_algorithm,
    "bubble_sort":          _sorting_algorithm,
    "merge_sort":           _sorting_algorithm,
    "quick_sort":           _sorting_algorithm,

    # ── Graph structures ───────────────────────────────────────────────────────
    "graph":                _graph,
    "undirected_graph":     _graph,
    "directed_graph":       _directed_graph,
    "digraph":              _directed_graph,
    "hash_table":           _hash_table,
    "hash_map":             _hash_table,
    "matrix":               _matrix,
    "2d_array":             _matrix,
    "neural_network":       _neural_network,
    "deep_learning":        _neural_network,
    "perceptron":           _neural_network,

    # ── Physical / scientific ──────────────────────────────────────────────────
    "molecule":             _molecule,
    "atom":                 _atom,
    "dna":                  _dna,
    "dna_helix":            _dna,
    "double_helix":         _dna,
    "solar_system":         _solar_system,
    "inclined_plane":       _inclined_plane,
    "ramp":                 _inclined_plane,
    "friction":             _inclined_plane,

    # ── Technology ─────────────────────────────────────────────────────────────
    "cpu":                  _cpu,
    "processor":            _cpu,
    "computer_architecture":_cpu,

    # ── Biology ────────────────────────────────────────────────────────────────
    "cell":                 _cell,
    "animal_cell":          _cell,
    "plant_cell":           _cell,

    # ── Type-level fallbacks (concept.type as key) ─────────────────────────────
    "algorithmic":          _binary_tree,
    "physical":             _molecule,
    "biological":           _cell,
}
