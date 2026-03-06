"""
physics_solver.py — Complete Physics Engine
Solvers: projectile, free_fall, pendulum, circular_motion, spring_shm,
         collision, relative_motion, electric_field, magnetic_force,
         pv_diagram, carnot, wave_superposition, standing_wave, refraction, lens
"""

import os
import math
import json
import httpx
import numpy as np


# ─── LLM PARAMETER EXTRACTION ────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a physics problem parser. Extract ALL numeric parameters and return ONLY valid JSON.

Return this structure:
{
  "problem_type": "<type>",
  "params": { ... },
  "description": "one line summary"
}

Problem types and their params:

MECHANICS:
- "projectile": v0(m/s), angle_deg, height(m), g(9.8)
- "free_fall": height(m), g(9.8), mass(kg)
- "pendulum": length(m), angle_deg, g(9.8), mass(kg)
- "circular_motion": radius(m), mass(kg), g(9.8)
- "spring_shm": k(N/m), mass(kg), amplitude(m)
- "collision": m1(kg), v1(m/s), m2(kg), v2(m/s), type("elastic"/"inelastic")
- "relative_motion": v_truck(m/s), v0(m/s), height(m)

THERMODYNAMICS:
- "pv_diagram": P1(Pa), V1(m3), T1(K), process("isothermal"/"adiabatic"/"isobaric"/"isochoric"), gamma(1.4)
- "carnot": T_hot(K), T_cold(K), Q_hot(J)

ELECTROMAGNETISM:
- "electric_field": q1(C), q2(C), separation(m), sign1(1 or -1), sign2(1 or -1)
- "magnetic_force": B(T), v(m/s), charge(C), mass(kg), q_sign(1 or -1)

WAVES:
- "wave_superposition": f1(Hz), A1, f2(Hz), A2, duration(s)
- "standing_wave": L(m), f_fundamental(Hz), harmonics(int)

OPTICS:
- "lens": f(m), d_o(m), h_o(m), type("convex"/"concave")
- "refraction": n1(float), n2(float), angle_inc_deg(float)

Extract ALL numeric values from the problem. Use sensible physics defaults if not stated.
Return ONLY the JSON object, no markdown, no explanation."""


async def extract_physics_params(chapter: str, problem: str) -> dict:
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return _fallback_params(chapter, problem)
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Chapter: {chapter}\nProblem: {problem}"},
                    ],
                    "max_tokens": 500,
                    "temperature": 0.05,
                }
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            if "```" in content:
                parts = content.split("```")
                content = parts[1] if len(parts) > 1 else parts[0]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())
    except Exception as e:
        print(f"[physics_solver] LLM failed: {e}")
        return _fallback_params(chapter, problem)


def _fallback_params(chapter: str, problem: str) -> dict:
    defaults = {
        'mechanics':        {"problem_type": "projectile",        "params": {"v0": 20, "angle_deg": 45, "height": 0, "g": 9.8}},
        'thermodynamics':   {"problem_type": "pv_diagram",        "params": {"P1": 101325, "V1": 0.001, "T1": 300, "process": "isothermal", "gamma": 1.4}},
        'electromagnetism': {"problem_type": "electric_field",    "params": {"q1": 1e-6, "q2": 1e-6, "separation": 2, "sign1": 1, "sign2": -1}},
        'waves':            {"problem_type": "wave_superposition","params": {"f1": 2, "A1": 1, "f2": 3, "A2": 1, "duration": 3}},
        'optics':           {"problem_type": "lens",              "params": {"f": 0.1, "d_o": 0.25, "h_o": 0.05, "type": "convex"}},
    }
    d = defaults.get(chapter, defaults['mechanics'])
    d["description"] = problem[:80]
    return d


# ─── MECHANICS ────────────────────────────────────────────────────────────────

def solve_projectile(params: dict) -> dict:
    v0    = float(params.get('v0', 20))
    angle = math.radians(float(params.get('angle_deg', 45)))
    h0    = float(params.get('height', 0))
    g     = float(params.get('g', 9.8))

    vx = v0 * math.cos(angle)
    vy = v0 * math.sin(angle)
    disc = vy**2 + 2 * g * h0
    t_total = max((vy + math.sqrt(max(0.0, disc))) / g, 0.5)

    steps = 80
    keyframes = []
    for i in range(steps + 1):
        t = t_total * i / steps
        x = vx * t
        y = h0 + vy * t - 0.5 * g * t**2
        keyframes.append({'t': round(t, 4), 'x': round(float(x), 4),
                           'y': round(float(max(0.0, y)), 4), 'z': 0.0})

    range_ = vx * t_total
    max_h  = h0 + (vy**2) / (2 * g) if g > 0 else h0

    return {
        'objects': [{'id': 'ball', 'shape': 'sphere', 'size': 0.4,
                     'color': '#f59e0b', 'label': 'Projectile',
                     'trail': True, 'keyframes': keyframes, 'loop': True}],
        'static_objects': [
            {'shape': 'plane', 'position': [range_/2, -0.1, 0],
             'rotation': [-math.pi/2, 0, 0],
             'width': max(range_ * 1.5, 20), 'depth': 8, 'color': '#1a3a1a'},
        ],
        'vectors': [
            {'origin': [0.0, float(h0), 0.0],
             'direction': [round(vx * 0.2, 3), round(vy * 0.2, 3), 0.0],
             'color': '#22c55e'},
        ],
        'solution': {
            'initial_velocity': f'{v0} m/s',
            'launch_angle':     f'{math.degrees(angle):.1f}°',
            'time_of_flight':   f'{t_total:.3f} s',
            'range':            f'{range_:.3f} m',
            'max_height':       f'{max_h:.3f} m',
            'v_x':              f'{vx:.3f} m/s',
            'v_y_initial':      f'{vy:.3f} m/s',
        }
    }


def solve_free_fall(params: dict) -> dict:
    h = float(params.get('height', 100))
    g = float(params.get('g', 9.8))
    t_total = math.sqrt(2 * h / g)
    v_final = g * t_total
    steps = 60
    keyframes = [{'t': round(t_total*i/steps, 4), 'x': 0.0,
                  'y': round(float(max(0.0, h - 0.5*g*(t_total*i/steps)**2)), 4), 'z': 0.0}
                 for i in range(steps + 1)]
    return {
        'objects': [{'id': 'obj', 'shape': 'sphere', 'size': 0.4,
                     'color': '#ef4444', 'label': 'Object',
                     'trail': True, 'keyframes': keyframes, 'loop': True}],
        'static_objects': [
            {'shape': 'plane', 'position': [0, -0.1, 0],
             'rotation': [-math.pi/2, 0, 0], 'width': 10, 'depth': 10, 'color': '#1a1a3a'},
        ],
        'vectors': [{'origin': [0.6, h/2, 0.0], 'direction': [0.0, -4.0, 0.0], 'color': '#ef4444'}],
        'solution': {
            'drop_height':    f'{h} m',
            'time_to_fall':   f'{t_total:.3f} s',
            'final_velocity': f'{v_final:.3f} m/s',
            'g':              f'{g} m/s²',
        }
    }


def solve_pendulum(params: dict) -> dict:
    L      = float(params.get('length', 2.0))
    theta0 = math.radians(float(params.get('angle_deg', 30)))
    g      = float(params.get('g', 9.8))
    omega  = math.sqrt(g / L)
    T      = 2 * math.pi / omega
    pivot_y = L + 1.0
    steps = 120
    t_total = T * 3

    keyframes = []
    for i in range(steps + 1):
        t     = t_total * i / steps
        theta = theta0 * math.cos(omega * t)
        x     = L * math.sin(theta)
        y     = pivot_y - L * math.cos(theta)
        keyframes.append({'t': round(t, 4), 'x': round(float(x), 4),
                           'y': round(float(y), 4), 'z': 0.0})
    return {
        'objects': [{'id': 'bob', 'shape': 'sphere', 'size': 0.3,
                     'color': '#6366f1', 'label': 'Bob',
                     'trail': False, 'keyframes': keyframes, 'loop': True}],
        'static_objects': [
            {'shape': 'box', 'position': [0.0, pivot_y + 0.2, 0.0], 'size': 0.2, 'color': '#888888'},
        ],
        'vectors': [],
        'solution': {
            'length':    f'{L} m',
            'period':    f'{T:.3f} s',
            'frequency': f'{1/T:.3f} Hz',
            'max_angle': f'{math.degrees(theta0):.1f}°',
            'omega':     f'{omega:.3f} rad/s',
        }
    }


def solve_circular_motion(params: dict) -> dict:
    r = float(params.get('radius', 10))
    m = float(params.get('mass', 1))
    g = float(params.get('g', 9.8))

    v_top    = math.sqrt(g * r)
    v_bottom = math.sqrt(5 * g * r)
    T        = 2 * math.pi * r / v_bottom
    cx, cy   = 0.0, r + 1.0
    steps    = 120

    keyframes = []
    for i in range(steps + 1):
        t     = T * i / steps
        angle = 2 * math.pi * t / T - math.pi / 2
        keyframes.append({'t': round(t, 4),
                           'x': round(float(cx + r * math.cos(angle)), 4),
                           'y': round(float(cy + r * math.sin(angle)), 4),
                           'z': 0.0})
    return {
        'objects': [{'id': 'mass', 'shape': 'sphere', 'size': 0.35,
                     'color': '#f59e0b', 'label': f'{m}kg',
                     'trail': False, 'keyframes': keyframes, 'loop': True}],
        'static_objects': [
            {'shape': 'box', 'position': [cx, cy, 0.0], 'size': 0.1, 'color': '#888888'},
        ],
        'vectors': [
            {'origin': [cx, cy - r, 0.0], 'direction': [0.0, -2.5, 0.0], 'color': '#ef4444'},
        ],
        'solution': {
            'radius':            f'{r} m',
            'mass':              f'{m} kg',
            'min_v_at_top':      f'{v_top:.3f} m/s',
            'min_v_at_bottom':   f'{v_bottom:.3f} m/s',
            'tension_at_bottom': f'{m*(g + v_bottom**2/r):.3f} N',
            'tension_at_top':    f'{max(0.0, m*(v_top**2/r - g)):.3f} N',
        }
    }


def solve_spring_shm(params: dict) -> dict:
    k = float(params.get('k', 10))
    m = float(params.get('mass', 1))
    A = float(params.get('amplitude', 1))

    omega   = math.sqrt(k / m)
    T       = 2 * math.pi / omega
    t_total = T * 3
    steps   = 120

    keyframes = [{'t': round(t_total*i/steps, 4),
                   'x': round(float(A * math.cos(omega * t_total * i / steps)), 4),
                   'y': 1.0, 'z': 0.0}
                 for i in range(steps + 1)]

    return {
        'objects': [{'id': 'mass', 'shape': 'box', 'size': 0.5,
                     'color': '#10b981', 'label': f'{m}kg',
                     'trail': False, 'keyframes': keyframes, 'loop': True}],
        'static_objects': [
            {'shape': 'box', 'position': [-(A + 1.5), 1.0, 0.0], 'size': 0.4, 'color': '#888888'},
        ],
        'vectors': [],
        'solution': {
            'spring_constant': f'{k} N/m',
            'mass':            f'{m} kg',
            'amplitude':       f'{A} m',
            'period':          f'{T:.3f} s',
            'frequency':       f'{1/T:.3f} Hz',
            'angular_freq':    f'{omega:.3f} rad/s',
            'max_velocity':    f'{A * omega:.3f} m/s',
            'max_KE':          f'{0.5 * k * A**2:.3f} J',
        }
    }


def solve_collision(params: dict) -> dict:
    m1    = float(params.get('m1', 2))
    v1    = float(params.get('v1', 5))
    m2    = float(params.get('m2', 1))
    v2    = float(params.get('v2', 0))
    ctype = str(params.get('type', 'elastic'))

    if 'elastic' in ctype.lower():
        v1f = ((m1 - m2)*v1 + 2*m2*v2) / (m1 + m2)
        v2f = ((m2 - m1)*v2 + 2*m1*v1) / (m1 + m2)
    else:
        v1f = v2f = (m1*v1 + m2*v2) / (m1 + m2)

    t_collision = 3.0
    steps = 80
    kf1, kf2 = [], []
    for i in range(steps + 1):
        t  = 5.0 * i / steps
        dt = max(0.0, t - t_collision)
        x1 = (-6 + v1 * min(t, t_collision) + v1f * dt)
        x2 = (6  + v2 * min(t, t_collision) + v2f * dt)
        kf1.append({'t': round(t, 3), 'x': round(float(x1), 3), 'y': 0.5, 'z': 0.0})
        kf2.append({'t': round(t, 3), 'x': round(float(x2), 3), 'y': 0.5, 'z': 0.0})

    return {
        'objects': [
            {'id': 'ball1', 'shape': 'sphere', 'size': 0.5 * math.sqrt(m1),
             'color': '#3b82f6', 'label': f'm₁={m1}kg',
             'trail': False, 'keyframes': kf1, 'loop': False},
            {'id': 'ball2', 'shape': 'sphere', 'size': 0.5 * math.sqrt(m2),
             'color': '#ef4444', 'label': f'm₂={m2}kg',
             'trail': False, 'keyframes': kf2, 'loop': False},
        ],
        'static_objects': [
            {'shape': 'plane', 'position': [0, -0.1, 0],
             'rotation': [-math.pi/2, 0, 0], 'width': 30, 'depth': 6, 'color': '#1a1a2a'},
        ],
        'vectors': [],
        'solution': {
            'collision_type':   ctype,
            'v1_initial':       f'{v1} m/s',
            'v2_initial':       f'{v2} m/s',
            'v1_final':         f'{v1f:.3f} m/s',
            'v2_final':         f'{v2f:.3f} m/s',
            'momentum_before':  f'{m1*v1 + m2*v2:.3f} kg·m/s',
            'momentum_after':   f'{m1*v1f + m2*v2f:.3f} kg·m/s',
            'KE_before':        f'{0.5*m1*v1**2 + 0.5*m2*v2**2:.3f} J',
            'KE_after':         f'{0.5*m1*v1f**2 + 0.5*m2*v2f**2:.3f} J',
        }
    }


def solve_relative_motion(params: dict) -> dict:
    v_truck  = float(params.get('v_truck', 30))
    v_bullet = float(params.get('v0', 300))
    v_abs    = v_truck + v_bullet
    steps    = 80

    truck_kf  = [{'t': round(5.0*i/steps, 3), 'x': round(float(v_truck*(5.0*i/steps)/10), 3), 'y': 0.8, 'z': 0.0} for i in range(steps+1)]
    bullet_kf = [{'t': round(5.0*i/steps, 3), 'x': round(float(v_bullet*(5.0*i/steps)/50), 3),'y': 0.8, 'z': 0.0} for i in range(steps+1)]

    return {
        'objects': [
            {'id': 'truck',  'shape': 'box',    'size': 1.5, 'color': '#3b82f6',
             'label': f'Truck {v_truck}m/s', 'trail': False, 'keyframes': truck_kf, 'loop': False},
            {'id': 'bullet', 'shape': 'sphere', 'size': 0.2, 'color': '#ef4444',
             'label': f'Bullet (abs) {v_abs}m/s', 'trail': True, 'keyframes': bullet_kf, 'loop': False},
        ],
        'static_objects': [
            {'shape': 'plane', 'position': [0, -0.1, 0],
             'rotation': [-math.pi/2, 0, 0], 'width': 60, 'depth': 8, 'color': '#1a1a1a'},
        ],
        'vectors': [
            {'origin': [0.0, 2.5, 0.0], 'direction': [2.0, 0.0, 0.0], 'color': '#3b82f6'},
            {'origin': [0.0, 1.5, 0.0], 'direction': [5.0, 0.0, 0.0], 'color': '#ef4444'},
        ],
        'solution': {
            'truck_velocity':        f'{v_truck} m/s',
            'bullet_vel_relative':   f'{v_bullet} m/s',
            'bullet_vel_absolute':   f'{v_abs} m/s',
        }
    }


# ─── THERMODYNAMICS ───────────────────────────────────────────────────────────

def solve_pv_diagram(params: dict) -> dict:
    P1      = float(params.get('P1', 101325))
    V1      = float(params.get('V1', 0.001))
    T1      = float(params.get('T1', 300))
    process = str(params.get('process', 'isothermal'))
    gamma   = float(params.get('gamma', 1.4))

    steps = 60
    V_arr = np.linspace(V1, V1 * 4, steps)

    if 'iso' in process.lower() and 'thermal' in process.lower():
        P_arr = P1 * V1 / V_arr
        label = f'Isothermal T={T1}K'
    elif 'adi' in process.lower():
        P_arr = P1 * (V1 / V_arr) ** gamma
        label = f'Adiabatic γ={gamma}'
    elif 'bar' in process.lower():
        P_arr = np.full(steps, P1)
        label = f'Isobaric P={P1:.0f}Pa'
    else:
        V_arr = np.full(steps, V1)
        P_arr = np.linspace(P1, P1 * 3, steps)
        label = f'Isochoric V={V1}m³'

    V_min, V_max = V_arr.min(), V_arr.max()
    P_min, P_max = P_arr.min(), P_arr.max()
    sx = 8.0 / max(V_max - V_min, 1e-10)
    sy = 6.0 / max(P_max - P_min, 1e-10)

    keyframes = [{'t': float(i),
                   'x': round(float((V_arr[i] - V_min) * sx - 4), 4),
                   'y': round(float((P_arr[i] - P_min) * sy + 0.5), 4),
                   'z': 0.0}
                 for i in range(steps)]

    work = float(np.trapz(P_arr, V_arr))

    return {
        'objects': [{'id': 'state', 'shape': 'sphere', 'size': 0.25,
                     'color': '#f59e0b', 'label': 'State',
                     'trail': True, 'keyframes': keyframes, 'loop': True}],
        'static_objects': [],
        'vectors': [],
        'solution': {
            'process':   label,
            'P_initial': f'{P1:.1f} Pa',
            'V_initial': f'{V1*1000:.3f} L',
            'T_initial': f'{T1} K',
            'work_done': f'{work:.4f} J',
        }
    }


def solve_carnot(params: dict) -> dict:
    T_hot  = float(params.get('T_hot', 500))
    T_cold = float(params.get('T_cold', 300))
    Q_hot  = float(params.get('Q_hot', 1000))

    eta   = 1 - T_cold / T_hot
    W     = eta * Q_hot
    Q_cold = Q_hot - W

    steps = 20
    V1, V2, V3, V4 = 1.0, 2.0, 3.2, 1.6
    P1 = 5.0

    def iso_pts(Va, Vb, Pa, n):
        vs = np.linspace(Va, Vb, n)
        return vs, Pa * Va / vs

    def adi_pts(Va, Vb, Pa, n, g=1.4):
        vs = np.linspace(Va, Vb, n)
        return vs, Pa * (Va/vs)**g

    s1v, s1p = iso_pts(V1, V2, P1, steps)
    s2v, s2p = adi_pts(V2, V3, s1p[-1], steps)
    s3v, s3p = iso_pts(V3, V4, s2p[-1], steps)
    s4v, s4p = adi_pts(V4, V1, s3p[-1], steps)

    all_v = np.concatenate([s1v, s2v, s3v, s4v])
    all_p = np.concatenate([s1p, s2p, s3p, s4p])

    sx = 8.0 / max(all_v.max() - all_v.min(), 1e-9)
    sy = 6.0 / max(all_p.max() - all_p.min(), 1e-9)

    keyframes = [{'t': float(i),
                   'x': round(float((all_v[i] - all_v.min()) * sx - 4), 4),
                   'y': round(float((all_p[i] - all_p.min()) * sy + 0.5), 4),
                   'z': 0.0}
                 for i in range(len(all_v))]

    return {
        'objects': [{'id': 'state', 'shape': 'sphere', 'size': 0.3,
                     'color': '#ef4444', 'label': 'Carnot',
                     'trail': True, 'keyframes': keyframes, 'loop': True}],
        'static_objects': [],
        'vectors': [],
        'solution': {
            'T_hot':      f'{T_hot} K',
            'T_cold':     f'{T_cold} K',
            'efficiency': f'{eta*100:.1f}%',
            'Q_hot':      f'{Q_hot} J',
            'work_done':  f'{W:.2f} J',
            'Q_rejected': f'{Q_cold:.2f} J',
        }
    }


# ─── ELECTROMAGNETISM ────────────────────────────────────────────────────────

def solve_electric_field(params: dict) -> dict:
    q1   = float(params.get('q1', 1e-6))
    q2   = float(params.get('q2', 1e-6))
    sep  = float(params.get('separation', 2))
    s1   = float(params.get('sign1', 1))
    s2   = float(params.get('sign2', -1))
    k_e  = 8.99e9

    F = k_e * abs(q1) * abs(q2) / sep**2

    colors = {1: '#ef4444', -1: '#3b82f6'}

    vectors = []
    for xi in np.linspace(-sep*1.5, sep*1.5, 6):
        for yi in np.linspace(-sep, sep, 6):
            if abs(xi + sep/2) < 0.4 and abs(yi) < 0.4: continue
            if abs(xi - sep/2) < 0.4 and abs(yi) < 0.4: continue
            r1x, r1y = xi + sep/2, yi
            r1 = math.sqrt(r1x**2 + r1y**2) + 1e-9
            r2x, r2y = xi - sep/2, yi
            r2 = math.sqrt(r2x**2 + r2y**2) + 1e-9
            Ex = k_e*q1*s1*r1x/r1**3 + k_e*q2*s2*r2x/r2**3
            Ey = k_e*q1*s1*r1y/r1**3 + k_e*q2*s2*r2y/r2**3
            mag = math.sqrt(Ex**2 + Ey**2)
            if mag > 0:
                vectors.append({'origin': [round(float(xi),3), round(float(yi),3), 0.0],
                                  'direction': [round(Ex/mag,3), round(Ey/mag,3), 0.0],
                                  'color': '#f59e0b'})

    return {
        'objects': [],
        'static_objects': [
            {'shape': 'sphere', 'position': [-sep/2, 0.0, 0.0], 'size': 0.35,
             'color': colors.get(int(s1), '#ef4444')},
            {'shape': 'sphere', 'position': [sep/2, 0.0, 0.0],  'size': 0.35,
             'color': colors.get(int(s2), '#3b82f6')},
        ],
        'vectors': vectors,
        'solution': {
            'q1':            f'{q1*1e6:.2f} μC ({"+" if s1>0 else "−"})',
            'q2':            f'{q2*1e6:.2f} μC ({"+" if s2>0 else "−"})',
            'separation':    f'{sep} m',
            'coulomb_force': f'{F:.4f} N',
            'interaction':   'Attractive' if s1 * s2 < 0 else 'Repulsive',
        }
    }


def solve_magnetic_force(params: dict) -> dict:
    B      = float(params.get('B', 0.5))
    v      = float(params.get('v', 1e6))
    charge = float(params.get('charge', 1.6e-19))
    mass   = float(params.get('mass', 1.67e-27))
    q_sign = float(params.get('q_sign', 1))

    r     = mass * v / (abs(charge) * B)
    T     = 2 * math.pi * mass / (abs(charge) * B)
    omega = abs(charge) * B / mass
    scale = min(r, 6.0)
    steps = 120

    keyframes = []
    for i in range(steps + 1):
        t     = T * i / steps
        angle = omega * t * q_sign
        keyframes.append({'t': round(t, 6),
                           'x': round(float(scale * math.sin(angle)), 4),
                           'y': round(float(scale * (1 - math.cos(angle))), 4),
                           'z': 0.0})
    return {
        'objects': [{'id': 'particle', 'shape': 'sphere', 'size': 0.2,
                     'color': '#f59e0b' if q_sign > 0 else '#3b82f6',
                     'label': 'Charged Particle',
                     'trail': True, 'keyframes': keyframes, 'loop': True}],
        'static_objects': [],
        'vectors': [
            {'origin': [0.0, scale, 0.0], 'direction': [0.0, 0.0, min(3*B, 4.0)], 'color': '#6366f1'},
        ],
        'solution': {
            'B_field':        f'{B} T',
            'velocity':       f'{v:.2e} m/s',
            'radius':         f'{r:.4f} m',
            'period':         f'{T:.4e} s',
            'cyclotron_freq': f'{1/T:.4e} Hz',
            'charge_sign':    '+' if q_sign > 0 else '−',
        }
    }


# ─── WAVES ────────────────────────────────────────────────────────────────────

def solve_wave_superposition(params: dict) -> dict:
    f1       = float(params.get('f1', 2))
    A1       = float(params.get('A1', 1))
    f2       = float(params.get('f2', 3))
    A2       = float(params.get('A2', 1))
    duration = float(params.get('duration', 3))

    steps = 200
    t_arr = np.linspace(0, duration, steps)
    y_arr = A1 * np.sin(2*math.pi*f1*t_arr) + A2 * np.sin(2*math.pi*f2*t_arr)

    x_scale = 8.0 / duration
    keyframes = [{'t': round(float(t_arr[i]), 4),
                   'x': round(float(t_arr[i] * x_scale - 4), 4),
                   'y': round(float(y_arr[i]) + 1, 4), 'z': 0.0}
                 for i in range(steps)]

    return {
        'objects': [{'id': 'wave', 'shape': 'sphere', 'size': 0.2,
                     'color': '#10b981', 'label': 'Superposition',
                     'trail': True, 'keyframes': keyframes, 'loop': True}],
        'static_objects': [],
        'vectors': [],
        'solution': {
            'f1':           f'{f1} Hz',
            'f2':           f'{f2} Hz',
            'A1':           str(A1),
            'A2':           str(A2),
            'beat_frequency': f'{abs(f1-f2)} Hz',
            'max_amplitude':  f'{A1+A2}',
        }
    }


def solve_standing_wave(params: dict) -> dict:
    L  = float(params.get('L', 1))
    f0 = float(params.get('f_fundamental', 100))
    n  = int(params.get('harmonics', 3))

    T     = 1.0 / f0
    steps = 100
    kf    = [{'t': round(T*i/steps, 6),
               'x': round(float(L/2 * 6 - 3), 4),
               'y': round(float(math.sin(math.pi) * math.cos(2*math.pi*f0*T*i/steps)) + 1, 4),
               'z': 0.0}
             for i in range(steps + 1)]

    return {
        'objects': [{'id': 'anti', 'shape': 'sphere', 'size': 0.2,
                     'color': '#8b5cf6', 'label': 'Antinode',
                     'trail': False, 'keyframes': kf, 'loop': True}],
        'static_objects': [
            {'shape': 'box', 'position': [-3.0, 1.0, 0.0], 'size': 0.2, 'color': '#888888'},
            {'shape': 'box', 'position': [3.0,  1.0, 0.0], 'size': 0.2, 'color': '#888888'},
        ],
        'vectors': [],
        'solution': {
            'string_length':   f'{L} m',
            'fundamental_f':   f'{f0} Hz',
            'harmonics':       str(n),
            'wavelength':      f'{2*L:.3f} m',
            'wave_speed':      f'{2*L*f0:.3f} m/s',
        }
    }


# ─── OPTICS ───────────────────────────────────────────────────────────────────

def solve_lens(params: dict) -> dict:
    f_raw     = float(params.get('f', 0.1))
    d_o       = float(params.get('d_o', 0.25))
    h_o       = float(params.get('h_o', 0.05))
    lens_type = str(params.get('type', 'convex'))

    f = -abs(f_raw) if 'concave' in lens_type.lower() else abs(f_raw)
    d_i = (f * d_o) / (d_o - f) if abs(d_o - f) > 1e-9 else 1e9
    m   = -d_i / d_o
    h_i = m * h_o

    scale = 5.0
    do_s  = min(d_o * scale, 8)
    di_s  = min(abs(d_i) * scale, 8) * (1 if d_i > 0 else -1)

    return {
        'objects': [],
        'static_objects': [
            {'shape': 'cylinder', 'position': [0.0, 1.0, 0.0], 'size': 0.1, 'color': '#60a5fa'},
            {'shape': 'box', 'position': [-do_s, abs(h_o)*scale/2, 0.0],
             'size': 0.15, 'height_ratio': abs(h_o)*scale*3, 'color': '#f59e0b'},
        ],
        'vectors': [
            {'origin': [-do_s, 0.0, 0.0], 'direction': [do_s, 0.0, 0.0],      'color': '#22c55e'},
            {'origin': [0.0, 0.0, 0.0],   'direction': [di_s, 0.0, 0.0],      'color': '#ef4444'},
        ],
        'solution': {
            'lens_type':      lens_type,
            'focal_length':   f'{f*100:.1f} cm',
            'object_distance':f'{d_o*100:.1f} cm',
            'image_distance': f'{d_i*100:.2f} cm',
            'magnification':  f'{m:.3f}×',
            'image_height':   f'{h_i*100:.2f} cm',
            'image_nature':   'Real & Inverted' if d_i > 0 else 'Virtual & Upright',
        }
    }


def solve_refraction(params: dict) -> dict:
    n1        = float(params.get('n1', 1.0))
    n2        = float(params.get('n2', 1.5))
    angle_inc = math.radians(float(params.get('angle_inc_deg', 30)))

    sin_r = n1 * math.sin(angle_inc) / n2
    if abs(sin_r) > 1.0:
        return {
            'objects': [], 'static_objects': [], 'vectors': [],
            'solution': {'result': 'Total Internal Reflection', 'n1': str(n1), 'n2': str(n2)}
        }

    angle_ref = math.asin(sin_r)
    crit = math.degrees(math.asin(n2/n1)) if n2 < n1 else None

    inc_x = math.sin(angle_inc) * 4
    inc_y = math.cos(angle_inc) * 4
    ref_x = math.sin(angle_ref) * 4
    ref_y = math.cos(angle_ref) * 4

    return {
        'objects': [],
        'static_objects': [
            {'shape': 'plane', 'position': [0.0, 0.0, 0.0],
             'rotation': [-math.pi/2, 0, 0], 'width': 12, 'depth': 10, 'color': '#1a2a4a'},
        ],
        'vectors': [
            {'origin': [-inc_x, inc_y, 0.0], 'direction': [inc_x, -inc_y, 0.0], 'color': '#f59e0b'},
            {'origin': [0.0, 0.0, 0.0],      'direction': [ref_x, ref_y, 0.0],  'color': '#10b981'},
            {'origin': [0.0, 4.0, 0.0],      'direction': [0.0, -4.0, 0.0],     'color': '#555555'},
        ],
        'solution': {
            'n1':              str(n1),
            'n2':              str(n2),
            'angle_incidence': f'{math.degrees(angle_inc):.1f}°',
            'angle_refraction':f'{math.degrees(angle_ref):.1f}°',
            'critical_angle':  f'{crit:.1f}°' if crit else 'N/A',
            'speed_in_medium': f'{3e8/n2:.3e} m/s',
        }
    }


# ─── SOLVER REGISTRY ─────────────────────────────────────────────────────────

SOLVERS = {
    # Mechanics
    'projectile':         solve_projectile,
    'free_fall':          solve_free_fall,
    'pendulum':           solve_pendulum,
    'circular_motion':    solve_circular_motion,
    'spring_shm':         solve_spring_shm,
    'collision':          solve_collision,
    'relative_motion':    solve_relative_motion,
    # Thermodynamics
    'pv_diagram':         solve_pv_diagram,
    'carnot':             solve_carnot,
    'isothermal':         solve_pv_diagram,
    'adiabatic':          solve_pv_diagram,
    'isobaric':           solve_pv_diagram,
    'isochoric':          solve_pv_diagram,
    # Electromagnetism
    'electric_field':     solve_electric_field,
    'magnetic_force':     solve_magnetic_force,
    'capacitor':          solve_electric_field,
    # Waves
    'wave_superposition': solve_wave_superposition,
    'standing_wave':      solve_standing_wave,
    # Optics
    'lens':               solve_lens,
    'mirror':             solve_lens,
    'refraction':         solve_refraction,
}


async def solve(chapter: str, problem: str) -> dict:
    extracted    = await extract_physics_params(chapter, problem)
    problem_type = extracted.get('problem_type', 'projectile')
    params       = extracted.get('params', {})
    description  = extracted.get('description', problem[:80])

    print(f"[physics_solver] type={problem_type} params={params}")

    solver = SOLVERS.get(problem_type, solve_projectile)
    result = solver(params)
    result['description']  = description
    result['problem_type'] = problem_type
    return result
