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
    eq = equation.strip()
    if '=' in eq:
        eq = eq.split('=', 1)[1].strip()

    xs = np.linspace(x_range[0], x_range[1], resolution)
    ys = np.linspace(y_range[0], y_range[1], resolution)

    # Build full grid (None for invalid points)
    grid = []
    for x in xs:
        row = []
        for y in ys:
            z = safe_eval(eq, {'x': float(x), 'y': float(y)})
            row.append(z)
        grid.append(row)

    # Flatten grid into points, track index map
    points = []
    index_map = {}  # (i,j) -> index in points list
    R = resolution
    for i in range(R):
        for j in range(R):
            z = grid[i][j]
            if z is not None:
                index_map[(i, j)] = len(points)
                points.append([float(xs[i]), float(z), float(ys[j])])

    # Only add triangles where all 4 corners exist
    triangles = []
    for i in range(R - 1):
        for j in range(R - 1):
            a = index_map.get((i,   j))
            b = index_map.get((i,   j+1))
            c = index_map.get((i+1, j))
            d = index_map.get((i+1, j+1))
            if a is not None and b is not None and c is not None:
                triangles.append([a, b, c])
            if b is not None and d is not None and c is not None:
                triangles.append([b, d, c])

    return {'plot_type': 'surface', 'points': points, 'triangles': triangles}

def plot_cylindrical(equation: str, resolution: int) -> dict:
    """Plot z = f(r, theta) in cylindrical coordinates."""
    eq = equation.strip()
    if '=' in eq:
        lhs, rhs = eq.split('=', 1)
        lhs, rhs = lhs.strip(), rhs.strip()
        if lhs.lower() == 'z':
            eq = rhs
        elif rhs.lower() == 'z':
            eq = lhs
        else:
            eq = rhs

    r_vals = np.linspace(0, 5, resolution)
    theta_vals = np.linspace(0, 2 * math.pi, resolution)

    # Build full grid
    grid = []
    for r in r_vals:
        row = []
        for theta in theta_vals:
            z = safe_eval(eq, {'r': float(r), 'theta': float(theta)})
            row.append(z)
        grid.append(row)

    # Flatten into points with index map
    points = []
    index_map = {}
    R = resolution
    for i in range(R):
        for j in range(R):
            z = grid[i][j]
            if z is not None:
                r = float(r_vals[i])
                theta = float(theta_vals[j])
                x = r * math.cos(theta)
                y = r * math.sin(theta)
                index_map[(i, j)] = len(points)
                points.append([x, float(z), y])

    triangles = []
    for i in range(R - 1):
        for j in range(R - 1):
            a = index_map.get((i,   j))
            b = index_map.get((i,   j+1))
            c = index_map.get((i+1, j))
            d = index_map.get((i+1, j+1))
            if a is not None and b is not None and c is not None:
                triangles.append([a, b, c])
            if b is not None and d is not None and c is not None:
                triangles.append([b, d, c])

    return {'plot_type': 'surface', 'points': points, 'triangles': triangles}


def plot_spherical(equation: str, resolution: int) -> dict:
    """Plot rho = f(phi, theta) in spherical coordinates."""
    eq = equation.strip()
    if '=' in eq:
        lhs, rhs = eq.split('=', 1)
        lhs, rhs = lhs.strip(), rhs.strip()
        # Handle both "rho = f(phi,theta)" and "f(phi,theta) = rho"
        if lhs.lower() == 'rho':
            eq = rhs
        elif rhs.lower() == 'rho':
            eq = lhs
        else:
            # Neither side is just "rho" — treat as implicit: lhs - rhs = 0, solve for rho
            eq = rhs

    phi_vals = np.linspace(0, math.pi, resolution)
    theta_vals = np.linspace(0, 2 * math.pi, resolution)

    # Build full grid
    grid = []
    for phi in phi_vals:
        row = []
        for theta in theta_vals:
            rho = safe_eval(eq, {'phi': float(phi), 'theta': float(theta), 'rho': 1.0})
            row.append(rho if (rho is not None and rho >= 0) else None)
        grid.append(row)

    # Flatten into points with index map
    points = []
    index_map = {}
    R = resolution
    for i in range(R):
        for j in range(R):
            rho = grid[i][j]
            if rho is not None:
                phi = float(phi_vals[i])
                theta = float(theta_vals[j])
                x = rho * math.sin(phi) * math.cos(theta)
                y = rho * math.cos(phi)
                z = rho * math.sin(phi) * math.sin(theta)
                index_map[(i, j)] = len(points)
                points.append([x, y, z])

    triangles = []
    for i in range(R - 1):
        for j in range(R - 1):
            a = index_map.get((i,   j))
            b = index_map.get((i,   j+1))
            c = index_map.get((i+1, j))
            d = index_map.get((i+1, j+1))
            if a is not None and b is not None and c is not None:
                triangles.append([a, b, c])
            if b is not None and d is not None and c is not None:
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

def plot_implicit(equation: str, x_range: list, y_range: list, resolution: int) -> dict:
    """
    Plot implicit surface f(x,y,z) = 0 using marching cubes algorithm.
    Equation examples:
      x**2 + y**2 + z**2 - 1        (sphere)
      x**2 + y**2 - z**2 - 1        (hyperboloid)
      x**2 + y**2 + z**2 - x*y*z    (custom)
    """
    eq = equation.strip()
    if '=' in eq:
        lhs, rhs = eq.split('=', 1)
        eq = f"({lhs.strip()}) - ({rhs.strip()})"  # convert to f(x,y,z) = 0 form

    z_range = x_range  # use same range for z
    res = max(10, min(50, resolution))  # cap at 50 for performance

    xs = np.linspace(x_range[0], x_range[1], res)
    ys = np.linspace(y_range[0], y_range[1], res)
    zs = np.linspace(z_range[0], z_range[1], res)

    # Evaluate f(x,y,z) at every grid point
    grid = np.zeros((res, res, res))
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            for k, z in enumerate(zs):
                val = safe_eval(eq, {'x': float(x), 'y': float(y), 'z': float(z)})
                grid[i, j, k] = val if val is not None else float('nan')

    # Marching cubes — find triangles where f changes sign
    points = []
    triangles = []

    def interp_vertex(p1, p2, v1, v2):
        """Interpolate vertex position where f=0 between p1 and p2."""
        if abs(v2 - v1) < 1e-10:
            return [(p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2]
        t = -v1 / (v2 - v1)
        return [p1[0] + t*(p2[0]-p1[0]),
                p1[1] + t*(p2[1]-p1[1]),
                p1[2] + t*(p2[2]-p1[2])]

    def add_triangle(pa, pb, pc):
        base = len(points)
        # THREE.js coord system: y is up, so swap y and z
        points.append([pa[0], pa[2], pa[1]])
        points.append([pb[0], pb[2], pb[1]])
        points.append([pc[0], pc[2], pc[1]])
        triangles.append([base, base+1, base+2])

    for i in range(res - 1):
        for j in range(res - 1):
            for k in range(res - 1):
                # 8 corners of the cube
                corners = [
                    (i,   j,   k),
                    (i+1, j,   k),
                    (i+1, j+1, k),
                    (i,   j+1, k),
                    (i,   j,   k+1),
                    (i+1, j,   k+1),
                    (i+1, j+1, k+1),
                    (i,   j+1, k+1),
                ]
                vals = [grid[c] for c in corners]
                pos  = [(float(xs[c[0]]), float(ys[c[1]]), float(zs[c[2]])) for c in corners]

                # Skip cubes with NaN
                if any(np.isnan(v) for v in vals):
                    continue

                # Find edges where sign changes
                edges = [
                    (0,1),(1,2),(2,3),(3,0),
                    (4,5),(5,6),(6,7),(7,4),
                    (0,4),(1,5),(2,6),(3,7),
                ]
                verts = {}
                for e, (a, b) in enumerate(edges):
                    if (vals[a] >= 0) != (vals[b] >= 0):
                        verts[e] = interp_vertex(pos[a], pos[b], vals[a], vals[b])

                if len(verts) < 3:
                    continue

                # Triangulate the intersection polygon
                vert_list = list(verts.values())
                for idx in range(1, len(vert_list) - 1):
                    add_triangle(vert_list[0], vert_list[idx], vert_list[idx+1])

    if not points:
        return {'error': 'No surface found. Check your equation or range.'}

    return {'plot_type': 'surface', 'points': points, 'triangles': triangles}

def plot_2d_contour(equation: str, x_range: list, y_range: list, resolution: int) -> dict:
    """Plot implicit 2D curve f(x,y) = 0 as a contour line."""
    eq = equation.strip()
    if '=' in eq:
        lhs, rhs = eq.split('=', 1)
        eq = f"({lhs.strip()}) - ({rhs.strip()})"

    res = max(50, min(200, resolution * 3))
    xs = np.linspace(x_range[0], x_range[1], res)
    ys = np.linspace(y_range[0], y_range[1], res)

    # Evaluate grid
    grid = np.zeros((res, res))
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            val = safe_eval(eq, {'x': float(x), 'y': float(y)})
            grid[i, j] = val if val is not None else float('nan')

    # Marching squares — find edges where sign changes
    points = []
    for i in range(res - 1):
        for j in range(res - 1):
            v00 = grid[i,   j]
            v10 = grid[i+1, j]
            v01 = grid[i,   j+1]
            v11 = grid[i+1, j+1]

            if any(np.isnan(v) for v in [v00, v10, v01, v11]):
                continue

            # Check each edge for sign change
            edges = [
                (v00, v10, xs[i], ys[j],   xs[i+1], ys[j]),    # bottom
                (v10, v11, xs[i+1], ys[j], xs[i+1], ys[j+1]),  # right
                (v01, v11, xs[i], ys[j+1], xs[i+1], ys[j+1]),  # top
                (v00, v01, xs[i], ys[j],   xs[i],   ys[j+1]),  # left
            ]

            cell_pts = []
            for va, vb, x1, y1, x2, y2 in edges:
                if (va >= 0) != (vb >= 0) and abs(vb - va) > 1e-10:
                    t = -va / (vb - va)
                    cell_pts.append([x1 + t*(x2-x1), y1 + t*(y2-y1), 0.0])

            if len(cell_pts) == 2:
                points.append(cell_pts[0])
                points.append(cell_pts[1])

    if not points:
        return {'error': 'No curve found. Check your equation or range.'}

    return {'plot_type': 'curve', 'points': points}

def plot_polar(equation: str, x_range: list, y_range: list, resolution: int) -> dict:
    """Plot r = f(theta) in polar coordinates as a 2D curve."""
    eq = equation.strip()
    if '=' in eq:
        eq = eq.split('=', 1)[1].strip()

    theta_vals = np.linspace(0, 2 * math.pi, resolution * 10)
    points = []
    for theta in theta_vals:
        r = safe_eval(eq, {'theta': float(theta), 'r': 1.0, 'pi': math.pi})
        if r is not None:
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            points.append([x, y, 0.0])

    return {'plot_type': 'curve', 'points': points}

def plot_implicit_extruded(equation: str, x_range: list, y_range: list, resolution: int) -> dict:
    """Extrude a 2D implicit curve f(x,y)=0 along z axis to make a 3D cylinder-like surface."""
    eq = equation.strip()
    if '=' in eq:
        lhs, rhs = eq.split('=', 1)
        eq = f"({lhs.strip()}) - ({rhs.strip()})"

    z_range = [-5, 5]
    res = max(10, min(50, resolution))
    xs = np.linspace(x_range[0], x_range[1], res)
    ys = np.linspace(y_range[0], y_range[1], res)
    zs = np.linspace(z_range[0], z_range[1], res)

    # Build 3D grid — f(x,y,z) = f(x,y) (z doesn't affect the equation)
    grid = np.zeros((res, res, res))
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            val = safe_eval(eq, {'x': float(x), 'y': float(y), 'z': 0.0})
            for k in range(res):
                grid[i, j, k] = val if val is not None else float('nan')

    # Reuse marching cubes
    points = []
    triangles = []

    def interp_vertex(p1, p2, v1, v2):
        if abs(v2 - v1) < 1e-10:
            return [(p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2]
        t = -v1 / (v2 - v1)
        return [p1[0]+t*(p2[0]-p1[0]), p1[1]+t*(p2[1]-p1[1]), p1[2]+t*(p2[2]-p1[2])]

    def add_triangle(pa, pb, pc):
        base = len(points)
        points.append([pa[0], pa[2], pa[1]])
        points.append([pb[0], pb[2], pb[1]])
        points.append([pc[0], pc[2], pc[1]])
        triangles.append([base, base+1, base+2])

    for i in range(res - 1):
        for j in range(res - 1):
            for k in range(res - 1):
                corners = [
                    (i,i+1,i,i+1,i,i+1,i,i+1),
                    (j,j,j+1,j+1,j,j,j+1,j+1),
                    (k,k,k,k,k+1,k+1,k+1,k+1),
                ]
                ci = [(corners[0][n], corners[1][n], corners[2][n]) for n in range(8)]
                vals = [grid[c] for c in ci]
                pos  = [(float(xs[c[0]]), float(ys[c[1]]), float(zs[c[2]])) for c in ci]

                if any(np.isnan(v) for v in vals):
                    continue

                edges = [
                    (0,1),(1,2),(2,3),(3,0),
                    (4,5),(5,6),(6,7),(7,4),
                    (0,4),(1,5),(2,6),(3,7),
                ]
                verts = {}
                for e, (a, b) in enumerate(edges):
                    if (vals[a] >= 0) != (vals[b] >= 0):
                        verts[e] = interp_vertex(pos[a], pos[b], vals[a], vals[b])

                if len(verts) < 3:
                    continue

                vert_list = list(verts.values())
                for idx in range(1, len(vert_list) - 1):
                    add_triangle(vert_list[0], vert_list[idx], vert_list[idx+1])

    if not points:
        return {'error': 'No surface found. Check your equation or range.'}

    return {'plot_type': 'surface', 'points': points, 'triangles': triangles}

def compute_plot(equation: str, coord_system: str, resolution: int,
                 x_range: list, y_range: list) -> dict:
    """Main entry point for plotting."""
    res = max(10, min(80, resolution))
    try:
        if coord_system == 'cartesian':
            eq_stripped = equation.strip()
            lhs = eq_stripped.split('=')[0].strip().lower() if '=' in eq_stripped else ''
            rhs = eq_stripped.split('=', 1)[1].strip() if '=' in eq_stripped else eq_stripped

            has_z = 'z' in lhs or 'z' in rhs

            if has_z:
                # True 3D implicit: x**2 + y**2 + z**2 = 1
                return plot_implicit(equation, x_range, y_range, res)
            elif lhs == 'z':
                # Explicit: z = f(x,y)
                return plot_cartesian(equation, x_range, y_range, res)
            else:
                # No z — in 3D this is a cylinder (extrude the 2D curve along z)
                return plot_implicit_extruded(equation, x_range, y_range, res)

        elif coord_system == 'cylindrical':
            return plot_cylindrical(equation, res)
        elif coord_system == 'spherical':
            return plot_spherical(equation, res)
        elif coord_system == 'parametric':
            return plot_parametric(equation, res)
        elif coord_system == 'vector':
            return plot_vector_field(equation, x_range, y_range, res)
        elif coord_system == 'cartesian2d':
            return plot_2d_contour(equation, x_range, y_range, res)
        elif coord_system == 'polar':
            return plot_polar(equation, x_range, y_range, res)
        elif coord_system == 'parametric2d':
            return plot_parametric(equation, res)
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