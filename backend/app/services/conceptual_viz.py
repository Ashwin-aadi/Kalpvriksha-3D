import math
import random
from app.models.schemas import ConceptResponse, FallbackResponse, ProceduralShape


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────

def generate(concept: ConceptResponse) -> FallbackResponse:
    key = concept.query.lower().strip().replace(' ', '_')

    # 1. Exact match in rules table
    rule_fn = VIZ_RULES.get(key)

    # 2. Partial keyword match
    if not rule_fn:
        rule_fn = _keyword_match(concept.query.lower())

    # 3. Smart fallback based on concept type / components
    if not rule_fn:
        rule_fn = _smart_default(concept)

    shapes = rule_fn(concept)

    return FallbackResponse(
        layer_used=3,
        layer_name='Conceptual Metaphor Visualization',
        result_type='conceptual',
        model=None,
        geometry=shapes,
        explanation=_explanation(concept, shapes),
    )


def _explanation(concept: ConceptResponse, shapes: list) -> str:
    shape_count = len([s for s in shapes if s.label])
    return (
        f'"{concept.query}" has no literal 3D form. '
        f'Rendered as a symbolic spatial metaphor with {shape_count} labeled nodes '
        f'representing its core aspects: {", ".join(concept.components[:4])}.'
    )


# ─────────────────────────────────────────────
#  KEYWORD ROUTER — catches synonyms & variants
# ─────────────────────────────────────────────

KEYWORD_MAP = {
    # Emotions — positive
    'love':        '_emotion_warm',
    'affection':   '_emotion_warm',
    'compassion':  '_emotion_warm',
    'empathy':     '_emotion_warm',
    'kindness':    '_emotion_warm',
    'gratitude':   '_emotion_warm',
    'joy':         '_emotion_burst',
    'happiness':   '_emotion_burst',
    'excitement':  '_emotion_burst',
    'euphoria':    '_emotion_burst',
    'bliss':       '_emotion_burst',
    'delight':     '_emotion_burst',
    'hope':        '_emotion_rise',
    'optimism':    '_emotion_rise',
    'inspiration': '_emotion_rise',
    'motivation':  '_emotion_rise',
    'ambition':    '_emotion_rise',
    'pride':       '_emotion_rise',

    # Emotions — negative
    'hate':        '_emotion_repel',
    'hatred':      '_emotion_repel',
    'anger':       '_emotion_explode',
    'rage':        '_emotion_explode',
    'fury':        '_emotion_explode',
    'wrath':       '_emotion_explode',
    'aggression':  '_emotion_explode',
    'fear':        '_emotion_collapse',
    'anxiety':     '_emotion_collapse',
    'dread':       '_emotion_collapse',
    'panic':       '_emotion_collapse',
    'phobia':      '_emotion_collapse',
    'sadness':     '_emotion_droop',
    'grief':       '_emotion_droop',
    'sorrow':      '_emotion_droop',
    'depression':  '_emotion_droop',
    'melancholy':  '_emotion_droop',
    'loneliness':  '_emotion_droop',
    'guilt':       '_emotion_collapse',
    'shame':       '_emotion_collapse',
    'jealousy':    '_emotion_tension',
    'envy':        '_emotion_tension',
    'resentment':  '_emotion_tension',
    'disgust':     '_emotion_repel',
    'contempt':    '_emotion_repel',

    # Emotions — complex
    'nostalgia':   '_emotion_orbit',
    'wonder':      '_emotion_orbit',
    'awe':         '_emotion_orbit',
    'curiosity':   '_emotion_orbit',
    'confusion':   '_emotion_chaos',
    'doubt':       '_emotion_tension',
    'trust':       '_node_link',
    'surprise':    '_emotion_burst',
    'anticipation':'_emotion_rise',
    'boredom':     '_emotion_droop',
    'calm':        '_emotion_calm',
    'peace':       '_emotion_calm',
    'serenity':    '_emotion_calm',
    'contentment': '_emotion_calm',

    # Relationships & social
    'friendship':  '_relationship',
    'family':      '_relationship',
    'community':   '_relationship',
    'society':     '_hierarchy',
    'culture':     '_node_link',
    'identity':    '_node_link',
    'belonging':   '_relationship',
    'isolation':   '_emotion_droop',
    'conflict':    '_emotion_tension',
    'war':         '_emotion_explode',
    'peace':       '_emotion_calm',
    'cooperation': '_relationship',
    'competition': '_emotion_tension',
    'power':       '_hierarchy',
    'authority':   '_hierarchy',
    'leadership':  '_hierarchy',

    # Philosophy & values
    'justice':     '_scales',
    'fairness':    '_scales',
    'equality':    '_scales',
    'freedom':     '_freedom',
    'liberty':     '_freedom',
    'truth':       '_node_link',
    'knowledge':   '_node_link',
    'wisdom':      '_node_link',
    'morality':    '_scales',
    'ethics':      '_scales',
    'consciousness':'_consciousness',
    'mind':        '_consciousness',
    'soul':        '_consciousness',
    'existence':   '_consciousness',
    'reality':     '_consciousness',
    'time':        '_time_flow',
    'infinity':    '_infinity',
    'chaos':       '_emotion_chaos',
    'order':       '_hierarchy',
    'balance':     '_scales',
    'harmony':     '_emotion_calm',
    'beauty':      '_emotion_warm',
    'evil':        '_emotion_repel',
    'good':        '_emotion_warm',
    'virtue':      '_node_link',
    'courage':     '_emotion_rise',
    'faith':       '_emotion_rise',
    'belief':      '_node_link',

    # Science abstracts
    'entropy':     '_entropy',
    'energy':      '_energy',
    'gravity':     '_gravity',
    'force':       '_energy',
    'magnetism':   '_duality',
    'electricity': '_energy',
    'light':       '_energy',
    'dark':        '_gravity',
    'space':       '_infinity',
    'universe':    '_infinity',
    'evolution':   '_flow',
    'revolution':  '_cycle',
    'cycle':       '_cycle',
    'growth':      '_emotion_rise',
    'decay':       '_emotion_droop',
    'complexity':  '_node_link',
    'emergence':   '_emotion_burst',

    # Systems & processes
    'democracy':   '_node_link',
    'capitalism':  '_hierarchy',
    'communism':   '_hierarchy',
    'feudalism':   '_hierarchy',
    'government':  '_hierarchy',
    'economy':     '_flow',
    'market':      '_flow',
    'network':     '_node_link',
    'system':      '_node_link',
    'process':     '_flow',
    'workflow':    '_flow',
    'pipeline':    '_flow',
    'supply_chain':'_flow',
    'ecosystem':   '_node_link',
    'language':    '_node_link',
    'memory':      '_emotion_orbit',
    'dream':       '_emotion_orbit',
    'creativity':  '_emotion_burst',
    'innovation':  '_emotion_burst',
    'art':         '_emotion_warm',
    'music':       '_emotion_warm',
}


def _keyword_match(query: str):
    for keyword, fn_name in KEYWORD_MAP.items():
        if keyword in query:
            return globals().get(fn_name)
    return None


def _smart_default(concept: ConceptResponse):
    """Pick best template based on concept type and component count."""
    t = concept.type
    n = len(concept.components)
    if t == 'abstract':
        return _node_link
    if t == 'algorithmic':
        return _flow
    if n <= 2:
        return _duality
    if n >= 6:
        return _node_link
    return _node_link


# ─────────────────────────────────────────────
#  EMOTION TEMPLATES
# ─────────────────────────────────────────────

def _emotion_warm(concept: ConceptResponse) -> list[ProceduralShape]:
    """Love, affection, compassion — warm concentric rings radiating outward."""
    shapes = []
    comps = concept.components[:6] or ['connection', 'warmth', 'care', 'bond']
    # Central glowing heart-like cluster
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[1.6, 1.6, 1.6], color='#E74C3C', label=concept.query))
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[2.2, 2.2, 2.2], color='#FF6B6B'))
    # Orbiting satellites at two radii
    for i, comp in enumerate(comps):
        angle = (2 * math.pi / len(comps)) * i
        r = 3.8 if i % 2 == 0 else 5.2
        y = 0.4 * math.sin(angle * 2)
        x, z = r * math.cos(angle), r * math.sin(angle)
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, y, z],
            scale=[0.6, 0.6, 0.6], color='#FF9EAA', label=comp))
        shapes.append(ProceduralShape(
            shape='cylinder', position=[x * 0.5, y * 0.5, z * 0.5],
            scale=[0.04, r * 0.95, 0.04], color='#FF6B6B'))
    return shapes


def _emotion_burst(concept: ConceptResponse) -> list[ProceduralShape]:
    """Joy, happiness, excitement — explosive outward burst pattern."""
    shapes = []
    comps = concept.components[:8] or ['elation', 'energy', 'smile', 'light']
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[1.2, 1.2, 1.2], color='#F1C40F', label=concept.query))
    # Rays shooting outward at random angles
    random.seed(42)
    for i, comp in enumerate(comps):
        angle_h = (2 * math.pi / len(comps)) * i
        angle_v = random.uniform(-0.6, 0.6)
        r = random.uniform(3.5, 5.5)
        x = r * math.cos(angle_h) * math.cos(angle_v)
        y = r * math.sin(angle_v)
        z = r * math.sin(angle_h) * math.cos(angle_v)
        color = ['#F1C40F', '#F39C12', '#E67E22', '#FF6B35'][i % 4]
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, y, z],
            scale=[0.55, 0.55, 0.55], color=color, label=comp))
        # Ray line from center
        shapes.append(ProceduralShape(
            shape='cylinder', position=[x * 0.5, y * 0.5, z * 0.5],
            scale=[0.04, r * 0.9, 0.04], color='#F39C12'))
    return shapes


def _emotion_rise(concept: ConceptResponse) -> list[ProceduralShape]:
    """Hope, optimism, ambition — ascending spiral upward."""
    shapes = []
    comps = concept.components[:7] or ['aspiration', 'growth', 'light', 'future']
    # Ascending spiral
    for i, comp in enumerate(comps):
        t = i / max(len(comps) - 1, 1)
        angle = t * 3 * math.pi
        r = 1.5 + t * 1.5
        x = r * math.cos(angle)
        z = r * math.sin(angle)
        y = -2.5 + t * 5.5
        size = 0.4 + t * 0.5
        brightness = ['#2980B9', '#3498DB', '#5DADE2', '#85C1E9', '#AED6F1', '#D6EAF8', '#EBF5FB'][i % 7]
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, y, z],
            scale=[size, size, size], color=brightness, label=comp))
        if i > 0:
            # Connect to previous
            prev_t = (i - 1) / max(len(comps) - 1, 1)
            prev_angle = prev_t * 3 * math.pi
            prev_r = 1.5 + prev_t * 1.5
            px = prev_r * math.cos(prev_angle)
            pz = prev_r * math.sin(prev_angle)
            py = -2.5 + prev_t * 5.5
            shapes.append(ProceduralShape(
                shape='cylinder',
                position=[(x + px) / 2, (y + py) / 2, (z + pz) / 2],
                scale=[0.05, 1.6, 0.05], color='#5DADE2'))
    # Goal sphere at top
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 3.5, 0],
        scale=[0.9, 0.9, 0.9], color='#F1C40F', label=concept.query))
    return shapes


def _emotion_droop(concept: ConceptResponse) -> list[ProceduralShape]:
    """Sadness, grief, depression — downward drooping cluster."""
    shapes = []
    comps = concept.components[:6] or ['emptiness', 'weight', 'silence', 'tears']
    # Central dim sphere
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 1, 0],
        scale=[1.3, 1.3, 1.3], color='#5D6D7E', label=concept.query))
    # Components hanging below
    for i, comp in enumerate(comps):
        angle = (2 * math.pi / len(comps)) * i
        x = 2.5 * math.cos(angle)
        z = 2.5 * math.sin(angle)
        drop = -1.5 - (i % 3) * 0.8
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, drop, z],
            scale=[0.5, 0.5, 0.5], color='#7F8C8D', label=comp))
        shapes.append(ProceduralShape(
            shape='cylinder', position=[x * 0.6, (1 + drop) / 2, z * 0.6],
            scale=[0.04, abs(1 - drop) * 0.9, 0.04], color='#626567'))
    return shapes


def _emotion_explode(concept: ConceptResponse) -> list[ProceduralShape]:
    """Anger, rage, fury — chaotic outward explosion with jagged spikes."""
    shapes = []
    comps = concept.components[:7] or ['intensity', 'heat', 'force', 'conflict']
    # Hot core
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[1.3, 1.3, 1.3], color='#C0392B', label=concept.query))
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[1.8, 1.8, 1.8], color='#E74C3C'))
    random.seed(99)
    for i, comp in enumerate(comps):
        angle_h = (2 * math.pi / len(comps)) * i + random.uniform(-0.4, 0.4)
        angle_v = random.uniform(-0.8, 0.8)
        r = random.uniform(3.0, 5.5)
        x = r * math.cos(angle_h) * math.cos(angle_v)
        y = r * math.sin(angle_v)
        z = r * math.sin(angle_h) * math.cos(angle_v)
        colors = ['#C0392B', '#E74C3C', '#E67E22', '#F39C12']
        shapes.append(ProceduralShape(
            shape='box', position=[x, y, z],
            scale=[0.5, 0.5, 0.5], color=colors[i % 4], label=comp))
        shapes.append(ProceduralShape(
            shape='cylinder', position=[x * 0.5, y * 0.5, z * 0.5],
            scale=[0.06, r * 0.85, 0.06], color='#E74C3C'))
    return shapes


def _emotion_collapse(concept: ConceptResponse) -> list[ProceduralShape]:
    """Fear, anxiety, dread — inward collapsing spiral."""
    shapes = []
    comps = concept.components[:6] or ['threat', 'unknown', 'vulnerability', 'tension']
    # Outer ring collapsing inward
    for i, comp in enumerate(comps):
        t = i / max(len(comps) - 1, 1)
        angle = t * 4 * math.pi
        r = 5.0 - t * 3.5
        x = r * math.cos(angle)
        z = r * math.sin(angle)
        y = t * -1.5
        size = 0.7 - t * 0.3
        color = ['#8E44AD', '#6C3483', '#4A235A', '#2C1654', '#1A0A30', '#0D0515'][i % 6]
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, y, z],
            scale=[size, size, size], color=color, label=comp))
    # Dark core
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, -1.5, 0],
        scale=[0.6, 0.6, 0.6], color='#1A0A30', label=concept.query))
    return shapes


def _emotion_repel(concept: ConceptResponse) -> list[ProceduralShape]:
    """Hate, disgust, contempt — two opposing clusters pushing apart."""
    shapes = []
    comps = concept.components[:6] or ['rejection', 'opposition', 'distance', 'barrier']
    half = len(comps) // 2 or 1
    # Left cluster (self)
    shapes.append(ProceduralShape(
        shape='sphere', position=[-3.5, 0, 0],
        scale=[1.1, 1.1, 1.1], color='#C0392B', label=concept.query))
    for i, comp in enumerate(comps[:half]):
        angle = (math.pi / (half + 1)) * (i + 1) - math.pi / 2
        x = -3.5 + 2.0 * math.cos(angle + math.pi)
        y = 2.0 * math.sin(angle)
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, y, 0],
            scale=[0.5, 0.5, 0.5], color='#E74C3C', label=comp))
    # Right cluster (target)
    shapes.append(ProceduralShape(
        shape='sphere', position=[3.5, 0, 0],
        scale=[1.1, 1.1, 1.1], color='#7F8C8D', label='other'))
    for i, comp in enumerate(comps[half:]):
        angle = (math.pi / (half + 1)) * (i + 1) - math.pi / 2
        x = 3.5 + 2.0 * math.cos(angle)
        y = 2.0 * math.sin(angle)
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, y, 0],
            scale=[0.5, 0.5, 0.5], color='#95A5A6', label=comp))
    # Repulsion barrier in middle
    for j in range(3):
        shapes.append(ProceduralShape(
            shape='box', position=[0, (j - 1) * 1.2, 0],
            scale=[0.15, 0.8, 0.8], color='#566573'))
    return shapes


def _emotion_tension(concept: ConceptResponse) -> list[ProceduralShape]:
    """Jealousy, envy, competition — two nodes pulling toward same target."""
    shapes = []
    comps = concept.components[:5] or ['desire', 'rivalry', 'comparison', 'want']
    # Desired object at center top
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 3, 0],
        scale=[0.9, 0.9, 0.9], color='#F1C40F', label='desired'))
    # Two competing nodes
    shapes.append(ProceduralShape(
        shape='sphere', position=[-3, -1, 0],
        scale=[1.0, 1.0, 1.0], color='#E74C3C', label=concept.query))
    shapes.append(ProceduralShape(
        shape='sphere', position=[3, -1, 0],
        scale=[1.0, 1.0, 1.0], color='#3498DB', label='rival'))
    # Tension lines to desired object
    shapes.append(ProceduralShape(
        shape='cylinder', position=[-1.5, 1, 0],
        scale=[0.06, 4.2, 0.06], color='#E74C3C'))
    shapes.append(ProceduralShape(
        shape='cylinder', position=[1.5, 1, 0],
        scale=[0.06, 4.2, 0.06], color='#3498DB'))
    # Satellites
    for i, comp in enumerate(comps):
        angle = (2 * math.pi / len(comps)) * i
        x = 5.5 * math.cos(angle)
        z = 5.5 * math.sin(angle)
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, 0, z],
            scale=[0.45, 0.45, 0.45], color='#F39C12', label=comp))
    return shapes


def _emotion_orbit(concept: ConceptResponse) -> list[ProceduralShape]:
    """Nostalgia, wonder, awe, curiosity — dreamy orbital rings."""
    shapes = []
    comps = concept.components[:8] or ['memory', 'mystery', 'distance', 'longing']
    # Central mystery sphere
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[1.2, 1.2, 1.2], color='#8E44AD', label=concept.query))
    # Three orbital rings
    radii = [3.0, 4.5, 6.0]
    colors = ['#9B59B6', '#6C3483', '#4A235A']
    for ring_i, (r, col) in enumerate(zip(radii, colors)):
        n_nodes = 4 + ring_i * 2
        for j in range(n_nodes):
            angle = (2 * math.pi / n_nodes) * j
            tilt = ring_i * 0.3
            x = r * math.cos(angle)
            y = r * math.sin(angle) * math.sin(tilt)
            z = r * math.sin(angle) * math.cos(tilt)
            comp_label = comps[j % len(comps)] if j < len(comps) else None
            shapes.append(ProceduralShape(
                shape='sphere', position=[x, y, z],
                scale=[0.3, 0.3, 0.3], color=col, label=comp_label))
    return shapes


def _emotion_chaos(concept: ConceptResponse) -> list[ProceduralShape]:
    """Confusion, chaos — scattered random arrangement."""
    shapes = []
    comps = concept.components[:8] or ['disorder', 'noise', 'uncertainty', 'scatter']
    random.seed(7)
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[1.0, 1.0, 1.0], color='#E67E22', label=concept.query))
    colors = ['#E74C3C', '#3498DB', '#2ECC71', '#F1C40F', '#9B59B6', '#1ABC9C', '#E67E22', '#E91E63']
    for i, comp in enumerate(comps):
        x = random.uniform(-5, 5)
        y = random.uniform(-3, 3)
        z = random.uniform(-4, 4)
        size = random.uniform(0.3, 0.8)
        shape_type = ['sphere', 'box', 'cylinder'][i % 3]
        shapes.append(ProceduralShape(
            shape=shape_type, position=[x, y, z],
            scale=[size, size, size], color=colors[i % len(colors)], label=comp))
    return shapes


def _emotion_calm(concept: ConceptResponse) -> list[ProceduralShape]:
    """Peace, serenity, calm — smooth concentric rings, perfectly spaced."""
    shapes = []
    comps = concept.components[:6] or ['stillness', 'breath', 'silence', 'balance']
    # Central calm sphere
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[1.0, 1.0, 1.0], color='#1ABC9C', label=concept.query))
    # Perfect concentric rings
    for ring_i in range(3):
        r = 2.5 + ring_i * 2.0
        n = 6 + ring_i * 2
        ring_color = ['#48C9B0', '#76D7C4', '#A3E4D7'][ring_i]
        for j in range(n):
            angle = (2 * math.pi / n) * j
            x = r * math.cos(angle)
            z = r * math.sin(angle)
            label = comps[j % len(comps)] if j < len(comps) and ring_i == 0 else None
            shapes.append(ProceduralShape(
                shape='sphere', position=[x, 0, z],
                scale=[0.3, 0.3, 0.3], color=ring_color, label=label))
    return shapes


# ─────────────────────────────────────────────
#  CONCEPT TEMPLATES
# ─────────────────────────────────────────────

def _node_link(concept: ConceptResponse) -> list[ProceduralShape]:
    """Default — central hub with orbiting component nodes."""
    shapes = []
    comps = concept.components[:8] or ['aspect_1', 'aspect_2', 'aspect_3']
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[1.4, 1.4, 1.4], color='#156082', label=concept.query))
    n = len(comps)
    for i, comp in enumerate(comps):
        angle = (2 * math.pi / n) * i
        x, z = 3.5 * math.cos(angle), 3.5 * math.sin(angle)
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, 0, z],
            scale=[0.75, 0.75, 0.75], color='#E97132', label=comp))
        shapes.append(ProceduralShape(
            shape='cylinder', position=[x * .5, 0, z * .5],
            scale=[0.05, 3.3, 0.05], color='#AAAAAA'))
    return shapes


def _hierarchy(concept: ConceptResponse) -> list[ProceduralShape]:
    """Top-down power structure."""
    shapes = []
    comps = concept.components[:7]
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 3, 0],
        scale=[1.0, 1.0, 1.0], color='#156082', label=concept.query))
    for i, comp in enumerate(comps):
        x = (i - len(comps) / 2) * 2.2
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, 0, 0],
            scale=[0.7, 0.7, 0.7], color='#E97132', label=comp))
        shapes.append(ProceduralShape(
            shape='cylinder', position=[x * .4, 1.5, 0],
            scale=[0.05, 3.2, 0.05], color='#BBBBBB'))
    return shapes


def _flow(concept: ConceptResponse) -> list[ProceduralShape]:
    """Left-to-right process flow."""
    shapes = []
    comps = concept.components[:6] or ['step_1', 'step_2', 'step_3']
    for i, comp in enumerate(comps):
        shapes.append(ProceduralShape(
            shape='box',
            position=[i * 2.5 - len(comps) * 1.25, 0, 0],
            scale=[0.9, 0.9, 0.9], color='#0F9ED5', label=comp))
        if i < len(comps) - 1:
            shapes.append(ProceduralShape(
                shape='cylinder',
                position=[i * 2.5 - len(comps) * 1.25 + 1.25, 0, 0],
                scale=[0.06, 1.5, 0.06], color='#AAAAAA'))
    return shapes


def _duality(concept: ConceptResponse) -> list[ProceduralShape]:
    """Two opposing or complementary forces."""
    shapes = []
    comps = concept.components[:4] or ['aspect_a', 'aspect_b']
    shapes.append(ProceduralShape(
        shape='sphere', position=[-2.5, 0, 0],
        scale=[1.1, 1.1, 1.1], color='#2980B9', label=comps[0] if comps else 'A'))
    shapes.append(ProceduralShape(
        shape='sphere', position=[2.5, 0, 0],
        scale=[1.1, 1.1, 1.1], color='#E74C3C', label=comps[1] if len(comps) > 1 else 'B'))
    shapes.append(ProceduralShape(
        shape='cylinder', position=[0, 0, 0],
        scale=[0.08, 4.8, 0.08], color='#888888'))
    # Central balance point
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[0.4, 0.4, 0.4], color='#F1C40F', label=concept.query))
    if len(comps) > 2:
        for i, comp in enumerate(comps[2:]):
            y = (i + 1) * 1.5
            shapes.append(ProceduralShape(
                shape='sphere', position=[0, y, 0],
                scale=[0.5, 0.5, 0.5], color='#9B59B6', label=comp))
    return shapes


def _scales(concept: ConceptResponse) -> list[ProceduralShape]:
    """Justice, balance, fairness — weighing scales metaphor."""
    shapes = []
    comps = concept.components[:6] or ['right', 'wrong', 'law', 'judgment']
    # Central pillar
    shapes.append(ProceduralShape(
        shape='cylinder', position=[0, 0, 0],
        scale=[0.1, 4.0, 0.1], color='#F1C40F'))
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 2.0, 0],
        scale=[0.4, 0.4, 0.4], color='#F1C40F', label=concept.query))
    # Crossbar
    shapes.append(ProceduralShape(
        shape='cylinder', position=[0, 2.0, 0],
        scale=[0.06, 6.0, 0.06], color='#D4AC0D'))
    # Left pan
    shapes.append(ProceduralShape(
        shape='cylinder', position=[-3.0, 0.5, 0],
        scale=[1.2, 0.08, 1.2], color='#D4AC0D'))
    # Right pan
    shapes.append(ProceduralShape(
        shape='cylinder', position=[3.0, 0.5, 0],
        scale=[1.2, 0.08, 1.2], color='#D4AC0D'))
    # Hang lines
    shapes.append(ProceduralShape(
        shape='cylinder', position=[-3.0, 1.2, 0],
        scale=[0.04, 1.5, 0.04], color='#888888'))
    shapes.append(ProceduralShape(
        shape='cylinder', position=[3.0, 1.2, 0],
        scale=[0.04, 1.5, 0.04], color='#888888'))
    # Items on scales
    half = len(comps) // 2
    for i, comp in enumerate(comps[:half]):
        shapes.append(ProceduralShape(
            shape='sphere', position=[-3.0 + (i - half / 2) * 0.8, 0.9, 0],
            scale=[0.35, 0.35, 0.35], color='#2980B9', label=comp))
    for i, comp in enumerate(comps[half:]):
        shapes.append(ProceduralShape(
            shape='sphere', position=[3.0 + (i - (len(comps) - half) / 2) * 0.8, 0.9, 0],
            scale=[0.35, 0.35, 0.35], color='#E74C3C', label=comp))
    return shapes


def _relationship(concept: ConceptResponse) -> list[ProceduralShape]:
    """Friendship, family, community — interconnected mesh of nodes."""
    shapes = []
    comps = concept.components[:7] or ['bond', 'trust', 'support', 'care']
    n = len(comps) + 1
    positions = []
    # Place nodes in circle
    for i in range(n):
        angle = (2 * math.pi / n) * i
        r = 3.5
        x = r * math.cos(angle)
        z = r * math.sin(angle)
        positions.append((x, 0, z))
        label = concept.query if i == 0 else comps[i - 1]
        color = '#156082' if i == 0 else '#27AE60'
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, 0, z],
            scale=[0.8, 0.8, 0.8], color=color, label=label))
    # Connect every node to every other (mesh)
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            p1, p2 = positions[i], positions[j]
            mid = [(p1[k] + p2[k]) / 2 for k in range(3)]
            dist = math.sqrt(sum((p1[k] - p2[k]) ** 2 for k in range(3)))
            if dist < 6.0:  # only connect nearby nodes
                shapes.append(ProceduralShape(
                    shape='cylinder', position=mid,
                    scale=[0.03, dist * 0.9, 0.03], color='#58D68D'))
    return shapes


def _freedom(concept: ConceptResponse) -> list[ProceduralShape]:
    """Freedom, liberty — open expanding structure, no constraints."""
    shapes = []
    comps = concept.components[:6] or ['choice', 'autonomy', 'expression', 'possibility']
    # Central small sphere (the self)
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[0.7, 0.7, 0.7], color='#3498DB', label=concept.query))
    # Rays shooting freely in all directions
    random.seed(42)
    for i, comp in enumerate(comps):
        angle_h = (2 * math.pi / len(comps)) * i
        angle_v = random.uniform(-1.0, 1.0)
        r = random.uniform(4.0, 7.0)
        x = r * math.cos(angle_h) * math.cos(angle_v)
        y = r * math.sin(angle_v)
        z = r * math.sin(angle_h) * math.cos(angle_v)
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, y, z],
            scale=[0.5, 0.5, 0.5], color='#5DADE2', label=comp))
        shapes.append(ProceduralShape(
            shape='cylinder', position=[x * 0.5, y * 0.5, z * 0.5],
            scale=[0.03, r * 0.85, 0.03], color='#85C1E9'))
    return shapes


def _consciousness(concept: ConceptResponse) -> list[ProceduralShape]:
    """Mind, consciousness, soul — layered nested spheres."""
    shapes = []
    comps = concept.components[:5] or ['awareness', 'thought', 'perception', 'self']
    layers = [
        (6.0, '#0D1B2A', None),
        (4.5, '#1B2631', None),
        (3.0, '#21618C', None),
        (1.8, '#2980B9', None),
        (0.8, '#AED6F1', concept.query),
    ]
    for r, color, label in layers:
        shapes.append(ProceduralShape(
            shape='sphere', position=[0, 0, 0],
            scale=[r, r, r], color=color, label=label))
    # Orbiting thoughts
    for i, comp in enumerate(comps):
        angle = (2 * math.pi / len(comps)) * i
        r = 5.0
        x = r * math.cos(angle)
        z = r * math.sin(angle)
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, 0, z],
            scale=[0.4, 0.4, 0.4], color='#F1C40F', label=comp))
    return shapes


def _time_flow(concept: ConceptResponse) -> list[ProceduralShape]:
    """Time — linear past → present → future arrow."""
    shapes = []
    comps = concept.components[:5] or ['past', 'present', 'future', 'moment', 'duration']
    colors = ['#7F8C8D', '#95A5A6', '#F1C40F', '#3498DB', '#2ECC71']
    for i, comp in enumerate(comps):
        x = (i - len(comps) / 2) * 2.8
        size = 0.4 + (i / len(comps)) * 0.6
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, 0, 0],
            scale=[size, size, size], color=colors[i % len(colors)], label=comp))
        if i < len(comps) - 1:
            shapes.append(ProceduralShape(
                shape='cylinder', position=[x + 1.4, 0, 0],
                scale=[0.06, 2.5, 0.06], color='#BDC3C7'))
    # Arrow head
    shapes.append(ProceduralShape(
        shape='box', position=[len(comps) * 1.4 - 0.5, 0, 0],
        scale=[0.4, 0.3, 0.3], color='#3498DB', label='→'))
    return shapes


def _infinity(concept: ConceptResponse) -> list[ProceduralShape]:
    """Infinity, universe, space — figure-8 lemniscate pattern."""
    shapes = []
    comps = concept.components[:6] or ['endless', 'boundless', 'eternal', 'vast']
    n_dots = 24
    for i in range(n_dots):
        t = (2 * math.pi / n_dots) * i
        # Lemniscate of Bernoulli parametric
        denom = 1 + math.sin(t) ** 2
        x = 4.0 * math.cos(t) / denom
        z = 4.0 * math.sin(t) * math.cos(t) / denom
        label = comps[i % len(comps)] if i < len(comps) else None
        shade = int(100 + (i / n_dots) * 155)
        color = f'#{shade:02X}{shade // 2:02X}FF'
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, 0, z],
            scale=[0.25, 0.25, 0.25], color='#5B2C8D', label=label))
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[0.6, 0.6, 0.6], color='#F1C40F', label=concept.query))
    return shapes


def _entropy(concept: ConceptResponse) -> list[ProceduralShape]:
    """Entropy — ordered center dissolving into chaos at edges."""
    shapes = []
    comps = concept.components[:6] or ['disorder', 'heat', 'randomness', 'dispersal']
    random.seed(21)
    # Ordered center
    for i in range(4):
        angle = (math.pi / 2) * i
        x, z = 1.5 * math.cos(angle), 1.5 * math.sin(angle)
        shapes.append(ProceduralShape(
            shape='box', position=[x, 0, z],
            scale=[0.5, 0.5, 0.5], color='#2980B9'))
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[0.6, 0.6, 0.6], color='#3498DB', label=concept.query))
    # Scattered outer chaos
    for i, comp in enumerate(comps):
        x = random.uniform(-6, 6)
        y = random.uniform(-2, 2)
        z = random.uniform(-5, 5)
        size = random.uniform(0.2, 0.5)
        shapes.append(ProceduralShape(
            shape=['sphere', 'box'][i % 2], position=[x, y, z],
            scale=[size, size, size], color='#E74C3C', label=comp))
    return shapes


def _energy(concept: ConceptResponse) -> list[ProceduralShape]:
    """Energy, force, electricity — radiating pulse pattern."""
    shapes = []
    comps = concept.components[:5] or ['power', 'wave', 'field', 'potential']
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[1.0, 1.0, 1.0], color='#F39C12', label=concept.query))
    # Concentric pulse rings at different radii
    for ring in range(4):
        r = 2.0 + ring * 1.8
        n = 8 + ring * 4
        alpha = 1.0 - ring * 0.2
        color = ['#F39C12', '#E67E22', '#D35400', '#BA4A00'][ring]
        for j in range(n):
            angle = (2 * math.pi / n) * j
            x = r * math.cos(angle)
            z = r * math.sin(angle)
            label = comps[j % len(comps)] if j < len(comps) and ring == 0 else None
            shapes.append(ProceduralShape(
                shape='sphere', position=[x, 0, z],
                scale=[0.2, 0.2, 0.2], color=color, label=label))
    return shapes


def _gravity(concept: ConceptResponse) -> list[ProceduralShape]:
    """Gravity, dark matter — objects being pulled toward a dense center."""
    shapes = []
    comps = concept.components[:6] or ['mass', 'attraction', 'field', 'curvature']
    # Dense dark core
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[1.5, 1.5, 1.5], color='#17202A', label=concept.query))
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[2.5, 2.5, 2.5], color='#1C2833'))
    random.seed(13)
    for i, comp in enumerate(comps):
        angle_h = (2 * math.pi / len(comps)) * i
        r = random.uniform(3.5, 6.5)
        x = r * math.cos(angle_h)
        z = r * math.sin(angle_h)
        y = random.uniform(-0.5, 0.5)
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, y, z],
            scale=[0.4, 0.4, 0.4], color='#5D6D7E', label=comp))
        # Pull line toward center
        shapes.append(ProceduralShape(
            shape='cylinder', position=[x * 0.5, y * 0.5, z * 0.5],
            scale=[0.03, r * 0.85, 0.03], color='#2E4053'))
    return shapes


def _cycle(concept: ConceptResponse) -> list[ProceduralShape]:
    """Cycle, revolution, loop — circular repeating pattern."""
    shapes = []
    comps = concept.components[:6] or ['phase_1', 'phase_2', 'phase_3', 'phase_4']
    n = len(comps)
    colors = ['#E74C3C', '#E67E22', '#F1C40F', '#2ECC71', '#3498DB', '#9B59B6']
    for i, comp in enumerate(comps):
        angle = (2 * math.pi / n) * i - math.pi / 2
        r = 3.5
        x = r * math.cos(angle)
        z = r * math.sin(angle)
        shapes.append(ProceduralShape(
            shape='sphere', position=[x, 0, z],
            scale=[0.8, 0.8, 0.8], color=colors[i % len(colors)], label=comp))
        # Arrow to next
        next_angle = (2 * math.pi / n) * ((i + 1) % n) - math.pi / 2
        nx = r * math.cos(next_angle)
        nz = r * math.sin(next_angle)
        shapes.append(ProceduralShape(
            shape='cylinder', position=[(x + nx) / 2, 0, (z + nz) / 2],
            scale=[0.05, 2.2, 0.05], color='#BDC3C7'))
    shapes.append(ProceduralShape(
        shape='sphere', position=[0, 0, 0],
        scale=[0.5, 0.5, 0.5], color='#F1C40F', label=concept.query))
    return shapes


# ─────────────────────────────────────────────
#  VIZ RULES TABLE — exact key → function
# ─────────────────────────────────────────────

VIZ_RULES = {
    # Emotions
    'love': _emotion_warm,
    'hate': _emotion_repel,
    'hatred': _emotion_repel,
    'anger': _emotion_explode,
    'rage': _emotion_explode,
    'fury': _emotion_explode,
    'joy': _emotion_burst,
    'happiness': _emotion_burst,
    'sadness': _emotion_droop,
    'grief': _emotion_droop,
    'fear': _emotion_collapse,
    'anxiety': _emotion_collapse,
    'hope': _emotion_rise,
    'despair': _emotion_droop,
    'nostalgia': _emotion_orbit,
    'wonder': _emotion_orbit,
    'awe': _emotion_orbit,
    'curiosity': _emotion_orbit,
    'jealousy': _emotion_tension,
    'envy': _emotion_tension,
    'disgust': _emotion_repel,
    'surprise': _emotion_burst,
    'excitement': _emotion_burst,
    'calm': _emotion_calm,
    'peace': _emotion_calm,
    'serenity': _emotion_calm,
    'boredom': _emotion_droop,
    'confusion': _emotion_chaos,
    'pride': _emotion_rise,
    'shame': _emotion_collapse,
    'guilt': _emotion_collapse,
    'empathy': _emotion_warm,
    'compassion': _emotion_warm,
    'gratitude': _emotion_warm,
    'affection': _emotion_warm,
    'loneliness': _emotion_droop,
    'melancholy': _emotion_droop,
    'euphoria': _emotion_burst,
    'panic': _emotion_collapse,
    'trust': _relationship,
    'courage': _emotion_rise,
    'ambition': _emotion_rise,
    'motivation': _emotion_rise,
    'inspiration': _emotion_rise,

    # Philosophy & values
    'justice': _scales,
    'fairness': _scales,
    'equality': _scales,
    'balance': _scales,
    'morality': _scales,
    'ethics': _scales,
    'freedom': _freedom,
    'liberty': _freedom,
    'consciousness': _consciousness,
    'mind': _consciousness,
    'soul': _consciousness,
    'time': _time_flow,
    'infinity': _infinity,
    'universe': _infinity,
    'entropy': _entropy,
    'chaos': _emotion_chaos,
    'order': _hierarchy,
    'harmony': _emotion_calm,
    'truth': _node_link,
    'wisdom': _node_link,
    'knowledge': _node_link,
    'creativity': _emotion_burst,
    'beauty': _emotion_warm,
    'evil': _emotion_repel,

    # Social & political
    'democracy': _node_link,
    'government': _hierarchy,
    'capitalism': _hierarchy,
    'communism': _hierarchy,
    'feudalism': _hierarchy,
    'society': _hierarchy,
    'culture': _node_link,
    'identity': _node_link,
    'friendship': _relationship,
    'family': _relationship,
    'community': _relationship,
    'conflict': _emotion_tension,
    'war': _emotion_explode,
    'cooperation': _relationship,
    'competition': _emotion_tension,
    'power': _hierarchy,
    'revolution': _cycle,
    'evolution': _flow,

    # Science abstracts
    'energy': _energy,
    'gravity': _gravity,
    'space': _infinity,
    'cycle': _cycle,
    'growth': _emotion_rise,
    'decay': _emotion_droop,
    'emergence': _emotion_burst,
    'complexity': _node_link,
    'duality': _duality,

    # Process
    'workflow': _flow,
    'supply_chain': _flow,
    'pipeline': _flow,
    'process': _flow,
    'memory': _emotion_orbit,
    'dream': _emotion_orbit,
}
