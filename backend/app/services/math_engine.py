"""
math_engine.py — 3D Mathematical Plotting Engine
Supports: Cartesian, Cylindrical, Spherical, Parametric, Vector Fields
Analysis: slope/gradient, area, divergence, curl
"""

import math
import numpy as np
from typing import Optional

# Safe math namespace for eval
SAFE_MATH = {
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan, 'atan2': math.atan2,
    'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
    'exp': math.exp, 'log': math.log, 'log2': math.log2, 'log10': math.log10,
    'sqrt': math.sqrt, 'abs': abs, 'pi': math.pi, 'e': math.e,
    'floor': math.floor, 'ceil': math.ceil, 'pow': math.pow,
}


def safe_eval(expr: str, variables: dict) -> float:
    """Safely evaluate a math expression."""
    namespace = {**SAFE_MATH, **variables}
    try:
        result = eval(expr, {"__builtins__": {}}, namespace)
        if not math.isfinite(result):
            return None
        return float(result)
    except Exception:
        return None


def plot_cartesian(equation: str, x_range: list, y_range: list, resolution: int) -> dict:
    """Plot z = f(x, y) surface."""
    # Parse equation: "z = x**2 + y**2" → extract RHS
    eq = equation.strip()
    if '=' in eq:
        eq = eq.split('=', 1)[1].strip()

    xs = np.linspace(x_range[0], x_range[1], resolution)
    ys = np.linspace(y_range[0], y_range[1], resolution)

    points = []
    for x in xs:
        for y in ys:
            z = safe_eval(eq, {'x': float(x), 'y': float(y)})
            if z is not None:
                points.append([float(x), float(z), float(y)])  # THREE.js: y is up

    # Build triangle indices
    triangles = []
    R = resolution
    for i in range(R - 1):
        for j in range(R - 1):
            a = i * R + j
            b = i * R + j + 1
            c = (i + 1) * R + j
            d = (i + 1) * R + j + 1
            triangles.append([a, b, c])
            triangles.append([b, d, c])

    return {'plot_type': 'surface', 'points': points, 'triangles': triangles}


def plot_cylindrical(equation: str, resolution: int) -> dict:
    """Plot z = f(r, theta) in cylindrical coordinates."""
    eq = equation.strip()
    if '=' in eq:
        eq = eq.split('=', 1)[1].strip()

    r_vals = np.linspace(0, 5, resolution)
    theta_vals = np.linspace(0, 2 * math.pi, resolution)

    points = []
    for r in r_vals:
        for theta in theta_vals:
            z = safe_eval(eq, {'r': float(r), 'theta': float(theta)})
            if z is not None:
                x = r * math.cos(theta)
                y = r * math.sin(theta)
                points.append([x, float(z), y])

    triangles = []
    R = resolution
    for i in range(R - 1):
        for j in range(R - 1):
            a = i * R + j
            b = i * R + j + 1
            c = (i + 1) * R + j
            d = (i + 1) * R + j + 1
            triangles.append([a, b, c])
            triangles.append([b, d, c])

    return {'plot_type': 'surface', 'points': points, 'triangles': triangles}


def plot_spherical(equation: str, resolution: int) -> dict:
    """Plot rho = f(phi, theta) in spherical coordinates."""
    eq = equation.strip()
    if '=' in eq:
        eq = eq.split('=', 1)[1].strip()

    phi_vals = np.linspace(0, math.pi, resolution)
    theta_vals = np.linspace(0, 2 * math.pi, resolution)

    points = []
    for phi in phi_vals:
        for theta in theta_vals:
            rho = safe_eval(eq, {'phi': float(phi), 'theta': float(theta), 'rho': 1.0})
            if rho is not None and rho >= 0:
                x = rho * math.sin(phi) * math.cos(theta)
                y = rho * math.cos(phi)
                z = rho * math.sin(phi) * math.sin(theta)
                points.append([x, y, z])

    triangles = []
    R = resolution
    for i in range(R - 1):
        for j in range(R - 1):
            a = i * R + j
            b = i * R + j + 1
            c = (i + 1) * R + j
            d = (i + 1) * R + j + 1
            triangles.append([a, b, c])
            triangles.append([b, d, c])

    return {'plot_type': 'surface', 'points': points, 'triangles': triangles}


def plot_parametric(equation: str, resolution: int) -> dict:
    """Plot parametric curve: x=f(t), y=g(t), z=h(t)"""
    # Parse: "x=cos(t), y=sin(t), z=t/3"
    parts = {}
    for part in equation.split(','):
        part = part.strip()
        if '=' in part:
            var, expr = part.split('=', 1)
            parts[var.strip()] = expr.strip()

    t_vals = np.linspace(0, 2 * math.pi * 2, resolution * 4)
    points = []
    for t in t_vals:
        x = safe_eval(parts.get('x', '0'), {'t': float(t)})
        y = safe_eval(parts.get('y', '0'), {'t': float(t)})
        z = safe_eval(parts.get('z', '0'), {'t': float(t)})
        if x is not None and y is not None and z is not None:
            points.append([x, y, z])

    return {'plot_type': 'curve', 'points': points}


def plot_vector_field(equation: str, x_range: list, y_range: list, resolution: int) -> dict:
    """Plot vector field F = [Fx, Fy, Fz]"""
    # Parse "F = [-y, x, 0]"
    eq = equation.strip()
    if '=' in eq:
        eq = eq.split('=', 1)[1].strip()
    # Remove brackets
    eq = eq.strip('[]')
    comps = [c.strip() for c in eq.split(',')]

    density = min(resolution // 4, 10)
    xs = np.linspace(x_range[0], x_range[1], density)
    ys = np.linspace(y_range[0], y_range[1], density)

    points = []
    for x in xs:
        for y in ys:
            for z_val in [-2, 0, 2]:
                ns = {'x': float(x), 'y': float(y), 'z': float(z_val)}
                fx = safe_eval(comps[0] if len(comps) > 0 else '0', ns) or 0
                fy = safe_eval(comps[1] if len(comps) > 1 else '0', ns) or 0
                fz = safe_eval(comps[2] if len(comps) > 2 else '0', ns) or 0
                mag = math.sqrt(fx**2 + fy**2 + fz**2)
                if mag > 0:
                    points.append({
                        'origin': [float(x), float(z_val), float(y)],
                        'direction': [fx/mag, fz/mag, fy/mag],
                        'magnitude': mag,
                    })

    return {'plot_type': 'vector_field', 'points': points}


def compute_plot(equation: str, coord_system: str, resolution: int,
                 x_range: list, y_range: list) -> dict:
    """Main entry point for plotting."""
    res = max(10, min(80, resolution))
    try:
        if coord_system == 'cartesian':
            return plot_cartesian(equation, x_range, y_range, res)
        elif coord_system == 'cylindrical':
            return plot_cylindrical(equation, res)
        elif coord_system == 'spherical':
            return plot_spherical(equation, res)
        elif coord_system == 'parametric':
            return plot_parametric(equation, res)
        elif coord_system == 'vector':
            return plot_vector_field(equation, x_range, y_range, res)
        else:
            return {'error': f'Unknown coordinate system: {coord_system}'}
    except Exception as e:
        return {'error': str(e)}


def analyze(equation: str, coord_system: str, analysis_type: str,
            point: list, x_range: list, y_range: list) -> dict:
    """Perform mathematical analysis at a point."""
    eq = equation.strip()
    if '=' in eq:
        eq = eq.split('=', 1)[1].strip()

    px, py = float(point[0]), float(point[1])
    h = 1e-5

    try:
        if analysis_type == 'slope':
            # Partial derivatives
            f   = safe_eval(eq, {'x': px,   'y': py})
            fx1 = safe_eval(eq, {'x': px+h, 'y': py})
            fx0 = safe_eval(eq, {'x': px-h, 'y': py})
            fy1 = safe_eval(eq, {'x': px,   'y': py+h})
            fy0 = safe_eval(eq, {'x': px,   'y': py-h})
            dfdx = (fx1 - fx0) / (2 * h) if fx1 and fx0 else None
            dfdy = (fy1 - fy0) / (2 * h) if fy1 and fy0 else None
            grad_mag = math.sqrt(dfdx**2 + dfdy**2) if dfdx and dfdy else None
            return {
                'type': 'Gradient / Slope',
                'point': f'({px}, {py})',
                'f(x,y)': f,
                'df/dx': dfdx,
                'df/dy': dfdy,
                'gradient_magnitude': grad_mag,
            }

        elif analysis_type == 'area':
            # Numerical integration over x at fixed y
            n = 1000
            xs = np.linspace(x_range[0], x_range[1], n)
            dx = (x_range[1] - x_range[0]) / n
            total = sum(
                abs(safe_eval(eq, {'x': float(x), 'y': py}) or 0) * dx
                for x in xs
            )
            return {
                'type': 'Area Under Curve',
                'y_slice': py,
                'x_range': str(x_range),
                'area': total,
            }

        elif analysis_type == 'divergence':
            # For vector field F=[Fx,Fy,Fz]: div F = dFx/dx + dFy/dy + dFz/dz
            parts = eq.strip('[]').split(',')
            if len(parts) < 2:
                return {'error': 'Divergence requires a vector field F=[Fx,Fy,Fz]'}
            ns = lambda x, y: {'x': x, 'y': y, 'z': 0.0}
            fx = lambda x, y: safe_eval(parts[0].strip(), ns(x, y)) or 0
            fy = lambda x, y: safe_eval(parts[1].strip(), ns(x, y)) or 0
            dFxdx = (fx(px+h, py) - fx(px-h, py)) / (2*h)
            dFydy = (fy(px, py+h) - fy(px, py-h)) / (2*h)
            div = dFxdx + dFydy
            return {
                'type': 'Divergence',
                'point': f'({px}, {py})',
                'dFx/dx': dFxdx,
                'dFy/dy': dFydy,
                'divergence': div,
            }

        elif analysis_type == 'curl':
            parts = eq.strip('[]').split(',')
            if len(parts) < 2:
                return {'error': 'Curl requires a vector field F=[Fx,Fy,Fz]'}
            ns = lambda x, y: {'x': x, 'y': y, 'z': 0.0}
            fx = lambda x, y: safe_eval(parts[0].strip(), ns(x, y)) or 0
            fy = lambda x, y: safe_eval(parts[1].strip(), ns(x, y)) or 0
            dFydx = (fy(px+h, py) - fy(px-h, py)) / (2*h)
            dFxdy = (fx(px, py+h) - fx(px, py-h)) / (2*h)
            curl_z = dFydx - dFxdy
            return {
                'type': 'Curl (z-component)',
                'point': f'({px}, {py})',
                'dFy/dx': dFydx,
                'dFx/dy': dFxdy,
                'curl_z': curl_z,
            }

    except Exception as e:
        return {'error': str(e)}

    return {'error': 'Unknown analysis type'}
