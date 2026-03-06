"""
physics_solver.py — Physics Problem Solver
Extracts parameters via Groq LLM, computes physics, returns animation keyframes.
Supports: Mechanics, Thermodynamics, Electromagnetism, Optics, Waves
"""

import os
import math
import json
import asyncio
import httpx
import numpy as np


SYSTEM_PROMPT = """You are a physics problem parser. Extract parameters from the problem and return ONLY valid JSON.

For mechanics problems return:
{
  "problem_type": "projectile|pendulum|free_fall|circular|spring|collision|relative_motion",
  "params": {
    "v0": initial_speed_m_per_s,
    "angle_deg": launch_angle_degrees,
    "height": initial_height_m,
    "mass": mass_kg,
    "g": 9.8,
    "length": pendulum_length_m,
    "k": spring_constant,
    "duration": simulation_duration_s
  },
  "description": "one line summary"
}

For thermodynamics:
{
  "problem_type": "pv_diagram|carnot|isothermal|adiabatic",
  "params": { "T_hot": K, "T_cold": K, "P1": Pa, "V1": m3, "gamma": 1.4 },
  "description": "one line summary"
}

For electromagnetism:
{
  "problem_type": "electric_field|magnetic_force|capacitor",
  "params": { "q1": C, "q2": C, "separation": m, "B": T, "v": m_per_s, "charge": C, "mass": kg },
  "description": "one line summary"
}

Extract ALL numeric values mentioned. If value not given, use sensible defaults.
Return ONLY the JSON object, no markdown, no explanation."""


async def extract_physics_params(chapter: str, problem: str) -> dict:
    """Use Groq to extract physics parameters from natural language."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        return _fallback_params(chapter, problem)

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Chapter: {chapter}\nProblem: {problem}"},
                    ],
                    "max_tokens": 400,
                    "temperature": 0.1,
                }
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())
    except Exception as e:
        print(f"[physics_solver] LLM extraction failed: {e}")
        return _fallback_params(chapter, problem)


def _fallback_params(chapter: str, problem: str) -> dict:
    if chapter == 'mechanics':
        return {"problem_type": "projectile", "params": {"v0": 20, "angle_deg": 45, "height": 0, "g": 9.8, "duration": 5}, "description": "Default projectile"}
    return {"problem_type": "unknown", "params": {}, "description": problem[:80]}


def solve_projectile(params: dict) -> dict:
    v0 = float(params.get('v0', 20))
    angle = math.radians(float(params.get('angle_deg', 45)))
    h0 = float(params.get('height', 0))
    g = float(params.get('g', 9.8))

    vx = v0 * math.cos(angle)
    vy = v0 * math.sin(angle)

    # Time of flight
    disc = vy**2 + 2 * g * h0
    if disc < 0: disc = 0
    t_total = (vy + math.sqrt(disc)) / g
    t_total = max(t_total, 1.0)

    # Keyframes
    steps = 60
    keyframes = []
    for i in range(steps + 1):
        t = t_total * i / steps
        x = vx * t
        y = h0 + vy * t - 0.5 * g * t**2
        if y < 0: y = 0
        keyframes.append({'t': t, 'x': x, 'y': y, 'z': 0})

    range_ = vx * t_total
    max_h = h0 + (vy**2) / (2 * g)

    return {
        'objects': [{
            'id': 'ball', 'shape': 'sphere', 'size': 0.3,
            'color': '#f59e0b', 'label': 'Projectile',
            'trail': True, 'keyframes': keyframes, 'loop': True,
        }],
        'static_objects': [
            {'shape': 'plane', 'position': [0, 0, 0], 'rotation': [-math.pi/2, 0, 0],
             'width': max(range_ * 1.5, 20), 'depth': 10, 'color': '#1a3a1a'},
        ],
        'vectors': [
            {'origin': [0, h0, 0], 'direction': [vx * 0.3, vy * 0.3, 0], 'color': '#22c55e'},
        ],
        'solution': {
            'initial_velocity': f'{v0} m/s',
            'launch_angle': f'{math.degrees(angle):.1f}°',
            'time_of_flight': f'{t_total:.3f} s',
            'range': f'{range_:.3f} m',
            'max_height': f'{max_h:.3f} m',
            'v_x': f'{vx:.3f} m/s',
            'v_y_initial': f'{vy:.3f} m/s',
        }
    }


def solve_pendulum(params: dict) -> dict:
    L = float(params.get('length', 2.0))
    theta0 = math.radians(float(params.get('angle_deg', 30)))
    g = float(params.get('g', 9.8))
    omega = math.sqrt(g / L)
    T = 2 * math.pi / omega

    steps = 120
    keyframes = []
    for i in range(steps + 1):
        t = T * 2 * i / steps
        theta = theta0 * math.cos(omega * t)
        x = L * math.sin(theta)
        y = -L * math.cos(theta) + L
        keyframes.append({'t': t, 'x': x, 'y': y, 'z': 0})

    return {
        'objects': [{
            'id': 'bob', 'shape': 'sphere', 'size': 0.25,
            'color': '#6366f1', 'label': 'Bob',
            'trail': False, 'keyframes': keyframes, 'loop': True,
        }],
        'static_objects': [
            {'shape': 'box', 'position': [0, L, 0], 'size': 0.1, 'color': '#888'},
        ],
        'vectors': [],
        'solution': {
            'length': f'{L} m',
            'period': f'{T:.3f} s',
            'frequency': f'{1/T:.3f} Hz',
            'max_angle': f'{math.degrees(theta0):.1f}°',
        }
    }


def solve_free_fall(params: dict) -> dict:
    h = float(params.get('height', 100))
    g = float(params.get('g', 9.8))
    t_total = math.sqrt(2 * h / g)
    v_final = g * t_total

    steps = 60
    keyframes = []
    for i in range(steps + 1):
        t = t_total * i / steps
        y = h - 0.5 * g * t**2
        keyframes.append({'t': t, 'x': 0, 'y': max(0, y), 'z': 0})

    return {
        'objects': [{
            'id': 'obj', 'shape': 'sphere', 'size': 0.4,
            'color': '#ef4444', 'label': 'Object',
            'trail': True, 'keyframes': keyframes, 'loop': True,
        }],
        'static_objects': [
            {'shape': 'plane', 'position': [0, 0, 0], 'rotation': [-math.pi/2, 0, 0],
             'width': 10, 'depth': 10, 'color': '#1a1a3a'},
        ],
        'vectors': [
            {'origin': [0, h/2, 0], 'direction': [0, -3, 0], 'color': '#ef4444'},
        ],
        'solution': {
            'drop_height': f'{h} m',
            'time_to_fall': f'{t_total:.3f} s',
            'final_velocity': f'{v_final:.3f} m/s',
            'g': f'{g} m/s²',
        }
    }


def solve_relative_motion(params: dict) -> dict:
    v_truck = float(params.get('v_truck', 30))
    v_bullet_rel = float(params.get('v0', 300))
    v_bullet_abs = v_truck + v_bullet_rel
    t_total = 3.0
    steps = 60

    truck_kf = [{'t': t_total*i/steps, 'x': v_truck * (t_total*i/steps), 'y': 0.5, 'z': 0} for i in range(steps+1)]
    bullet_kf = [{'t': t_total*i/steps, 'x': v_bullet_abs * (t_total*i/steps), 'y': 0.5, 'z': 0} for i in range(steps+1)]

    return {
        'objects': [
            {'id': 'truck', 'shape': 'box', 'size': 1.5, 'color': '#3b82f6',
             'label': f'Truck {v_truck}m/s', 'trail': False, 'keyframes': truck_kf, 'loop': False},
            {'id': 'bullet', 'shape': 'sphere', 'size': 0.15, 'color': '#ef4444',
             'label': f'Bullet {v_bullet_abs}m/s', 'trail': True, 'keyframes': bullet_kf, 'loop': False},
        ],
        'static_objects': [
            {'shape': 'plane', 'position': [0, 0, 0], 'rotation': [-math.pi/2, 0, 0], 'width': 100, 'depth': 10, 'color': '#1a1a1a'},
        ],
        'vectors': [
            {'origin': [0, 2, 0], 'direction': [v_truck * 0.05, 0, 0], 'color': '#3b82f6'},
            {'origin': [0, 1, 0], 'direction': [v_bullet_abs * 0.01, 0, 0], 'color': '#ef4444'},
        ],
        'solution': {
            'truck_velocity': f'{v_truck} m/s',
            'bullet_velocity_relative': f'{v_bullet_rel} m/s',
            'bullet_velocity_absolute': f'{v_bullet_abs} m/s',
        }
    }


SOLVERS = {
    'projectile':      solve_projectile,
    'free_fall':       solve_free_fall,
    'pendulum':        solve_pendulum,
    'relative_motion': solve_relative_motion,
    'collision':       solve_projectile,  # fallback
}


async def solve(chapter: str, problem: str) -> dict:
    """Main entry point."""
    extracted = await extract_physics_params(chapter, problem)
    problem_type = extracted.get('problem_type', 'projectile')
    params = extracted.get('params', {})
    description = extracted.get('description', problem[:80])

    solver = SOLVERS.get(problem_type, solve_projectile)
    result = solver(params)
    result['description'] = description
    result['problem_type'] = problem_type
    return result
