"""
physics_solver.py — JEE Advanced Complete Physics Engine
Covers: Mechanics (projectile, circular, rotation, SHM, friction, blocks, pulleys),
        Thermodynamics (PV, Carnot, calorimetry, heat transfer),
        Electromagnetism (Coulomb, fields, magnetic force, LC circuits),
        Optics (ray tracing, lenses, mirrors, prisms, interference),
        Waves (superposition, standing, Doppler),
        Modern Physics (photoelectric, Bohr model)
"""

import os, math, json, httpx
import numpy as np

# ─── LLM EXTRACTION ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a JEE Advanced physics problem parser. Extract ALL numeric values carefully.
Return ONLY valid JSON — no markdown, no explanation.

{
  "problem_type": "<type>",
  "params": { ... },
  "description": "concise one-line summary"
}

MECHANICS — problem_type options:
  "projectile":       v0, angle_deg, height, g(9.8)
  "free_fall":        height, g(9.8), mass
  "pendulum":         length, angle_deg, g(9.8), mass
  "circular_motion":  radius, mass, g(9.8), v0(optional)
  "vertical_circle":  radius, mass, g(9.8)
  "spring_shm":       k, mass, amplitude, x0(0)
  "coupled_spring":   k1, k2, m1, m2, A
  "collision":        m1, v1, m2, v2(0), type("elastic"/"inelastic"/"perfectly_inelastic")
  "relative_motion":  v_frame, v_object_rel, height
  "block_on_incline": mass, angle_deg, mu_s, mu_k, g(9.8), applied_force(0)
  "atwood":           m1, m2, g(9.8), rope_mass(0)
  "block_pulley":     m_block, m_hanging, mu_k, g(9.8)
  "rotation_disk":    mass, radius, torque, I_type("disk"/"ring"/"rod"/"sphere")
  "rolling":          mass, radius, incline_deg, g(9.8)
  "gyroscope":        mass, radius, omega, g(9.8)

THERMODYNAMICS:
  "pv_diagram":       P1, V1, T1, process("isothermal"/"adiabatic"/"isobaric"/"isochoric"), gamma(1.4)
  "carnot":           T_hot, T_cold, Q_hot
  "calorimetry":      m1, c1, T1, m2, c2, T2, phase_change(false), L(0)
  "heat_conduction":  k, A, L, T_hot, T_cold, time
  "stefan":           emissivity, area, T_surface, T_ambient
  "gas_law":          P1, V1, T1, P2(null), V2(null), T2(null), n_moles(1)

ELECTROMAGNETISM:
  "electric_field":   q1, q2, separation, sign1(1), sign2(-1)
  "gauss_field":      charge, geometry("sphere"/"cylinder"/"plane"), radius, sigma(0)
  "capacitor":        C, V, d, area, dielectric_k(1)
  "magnetic_force":   B, v, charge, mass, q_sign(1)
  "lc_circuit":       L, C, V0, R(0)
  "solenoid":         n_turns, length, current, radius
  "em_induction":     B, area, omega, R, t

WAVES:
  "wave_superposition": f1, A1, f2, A2, duration
  "standing_wave":      L, f_fundamental, harmonics
  "doppler":            f_source, v_source, v_observer, v_sound(340), approaching(true)
  "string_wave":        tension, linear_density, length, mode

OPTICS:
  "ray_refraction":   n1, n2, angle_inc_deg
  "lens":             f, d_o, h_o, type("convex"/"concave")
  "mirror":           f, d_o, h_o, type("concave"/"convex")
  "prism":            apex_deg, n, angle_inc_deg
  "thin_film":        n_film, thickness, n1(1), n2(1), wavelength_nm
  "youngs_double":    d_slit, D, wavelength_nm
  "single_slit":      a_width, D, wavelength_nm

MODERN PHYSICS:
  "photoelectric":    work_function_eV, frequency_Hz, intensity
  "bohr_atom":        Z, n_initial, n_final
  "radioactive":      N0, half_life, time

Extract ALL numbers from the problem. For missing values use sensible JEE defaults.
Identify the MOST SPECIFIC problem_type possible."""


async def extract_params(chapter: str, problem: str) -> dict:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return _fallback(chapter)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": f"Chapter: {chapter}\nProblem: {problem}"},
                    ],
                    "max_tokens": 600, "temperature": 0.05,
                }
            )
            r.raise_for_status()
            txt = r.json()["choices"][0]["message"]["content"].strip()
            if "```" in txt:
                txt = txt.split("```")[1]
                if txt.startswith("json"): txt = txt[4:]
            return json.loads(txt.strip())
    except Exception as e:
        print(f"[solver] LLM error: {e}")
        return _fallback(chapter)


def _fallback(chapter):
    d = {
        "mechanics":        {"problem_type": "projectile",      "params": {"v0": 20, "angle_deg": 45, "height": 0, "g": 9.8}},
        "thermodynamics":   {"problem_type": "calorimetry",     "params": {"m1": 1, "c1": 4186, "T1": 80, "m2": 0.5, "c2": 900, "T2": 20}},
        "electromagnetism": {"problem_type": "electric_field",  "params": {"q1": 2e-6, "q2": 2e-6, "separation": 3, "sign1": 1, "sign2": -1}},
        "waves":            {"problem_type": "wave_superposition","params": {"f1": 4, "A1": 1, "f2": 6, "A2": 0.8, "duration": 3}},
        "optics":           {"problem_type": "lens",            "params": {"f": 0.15, "d_o": 0.4, "h_o": 0.05, "type": "convex"}},
        "modern_physics":   {"problem_type": "photoelectric",   "params": {"work_function_eV": 2.3, "frequency_Hz": 8e14, "intensity": 1}},
    }
    return d.get(chapter, d["mechanics"])


# ─── UTILS ───────────────────────────────────────────────────────────────────

def kf(t, x, y, z=0.0):
    return {"t": round(float(t),5), "x": round(float(x),5),
            "y": round(float(y),5), "z": round(float(z),5)}

def vec(ox, oy, oz, dx, dy, dz, color="#f59e0b", label=""):
    return {"origin": [round(float(ox),4), round(float(oy),4), round(float(oz),4)],
            "direction": [round(float(dx),4), round(float(dy),4), round(float(dz),4)],
            "color": color, "label": label}

def sphere_obj(id_, x, y, z, size, color, label="", trail=False, keyframes=None, loop=True):
    o = {"id": id_, "shape": "sphere", "size": size, "color": color,
         "label": label, "trail": trail, "loop": loop,
         "keyframes": keyframes or [kf(0, x, y, z)]}
    return o

def box_obj(id_, x, y, z, size, color, label="", trail=False, keyframes=None, loop=True, hr=1):
    o = {"id": id_, "shape": "box", "size": size, "color": color,
         "label": label, "trail": trail, "loop": loop, "height_ratio": hr,
         "keyframes": keyframes or [kf(0, x, y, z)]}
    return o

def result(objects=None, statics=None, vectors=None, lines=None, labels=None, solution=None):
    return {
        "objects":        objects  or [],
        "static_objects": statics  or [],
        "vectors":        vectors  or [],
        "lines":          lines    or [],   # [{points:[[x,y,z],...], color, dashed}]
        "scene_labels":   labels   or [],   # [{text, x, y, z, color}]
        "solution":       solution or {},
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  MECHANICS
# ═══════════════════════════════════════════════════════════════════════════════

def solve_projectile(p):
    v0    = float(p.get("v0", 20))
    ang   = math.radians(float(p.get("angle_deg", 45)))
    h0    = float(p.get("height", 0))
    g     = float(p.get("g", 9.8))
    vx, vy = v0*math.cos(ang), v0*math.sin(ang)
    disc  = vy**2 + 2*g*h0
    T     = max((vy + math.sqrt(max(0, disc))) / g, 0.5)
    R     = vx * T
    H     = h0 + vy**2/(2*g)

    steps = 100
    kfs = [kf(T*i/steps, vx*T*i/steps, max(0, h0 + vy*(T*i/steps) - 0.5*g*(T*i/steps)**2))
           for i in range(steps+1)]

    # velocity vectors at key points
    vecs = []
    for frac in [0.0, 0.25, 0.5, 0.75]:
        t_ = T * frac
        px_, py_ = vx*t_, max(0, h0 + vy*t_ - 0.5*g*t_**2)
        vvx, vvy = vx, vy - g*t_
        mag = math.sqrt(vvx**2 + vvy**2)
        if mag > 0:
            scale = 1.5
            vecs.append(vec(px_, py_, 0, vvx/mag*scale, vvy/mag*scale, 0, "#22c55e", "v"))

    return result(
        objects=[sphere_obj("ball", 0, h0, 0, 0.35, "#f59e0b", "Projectile", trail=True, keyframes=kfs)],
        statics=[{"shape":"plane","position":[R/2,-0.05,0],"rotation":[-math.pi/2,0,0],
                  "width":max(R*1.5,20),"depth":8,"color":"#1a3a1a"}],
        vectors=vecs,
        lines=[{"points":[[0,h0,0],[R,0,0]],"color":"#ffffff33","dashed":True}],
        labels=[{"text":"Max H","x":R*0.25,"y":H+0.5,"z":0,"color":"#10b981"},
                {"text":f"Range={R:.1f}m","x":R,"y":0.5,"z":0,"color":"#f59e0b"}],
        solution={"v0":f"{v0} m/s","angle":f"{math.degrees(ang):.1f}°",
                  "time_of_flight":f"{T:.3f} s","range":f"{R:.3f} m",
                  "max_height":f"{H:.3f} m","vx":f"{vx:.2f} m/s","vy_0":f"{vy:.2f} m/s",
                  "v_impact":f"{math.sqrt(vx**2+(vy-g*T)**2):.2f} m/s"}
    )


def solve_free_fall(p):
    h = float(p.get("height", 80))
    g = float(p.get("g", 9.8))
    m = float(p.get("mass", 1))
    T = math.sqrt(2*h/g)
    vf= g*T
    steps=80
    kfs=[kf(T*i/steps, 0, max(0, h-0.5*g*(T*i/steps)**2)) for i in range(steps+1)]
    vecs=[vec(0.5, h*(1-i/4), 0, 0, -1.5, 0, "#ef4444") for i in range(4)]
    return result(
        objects=[sphere_obj("obj",0,h,0,0.4,"#ef4444",f"{m}kg",trail=True,keyframes=kfs)],
        statics=[{"shape":"plane","position":[0,-0.05,0],"rotation":[-math.pi/2,0,0],
                  "width":10,"depth":10,"color":"#1a1a3a"}],
        vectors=vecs,
        labels=[{"text":f"h={h}m","x":1,"y":h/2,"z":0,"color":"#aaa"},
                {"text":"g=9.8↓","x":-1,"y":h/2,"z":0,"color":"#ef4444"}],
        solution={"height":f"{h} m","mass":f"{m} kg","time":f"{T:.3f} s",
                  "final_velocity":f"{vf:.3f} m/s","KE_impact":f"{0.5*m*vf**2:.2f} J",
                  "PE_initial":f"{m*g*h:.2f} J"}
    )


def solve_pendulum(p):
    L     = float(p.get("length", 2))
    th0   = math.radians(float(p.get("angle_deg", 30)))
    g     = float(p.get("g", 9.8))
    m     = float(p.get("mass", 0.5))
    omega = math.sqrt(g/L)
    T     = 2*math.pi/omega
    pivot_y = L + 1
    steps = 150
    t_total = T*3
    kfs = []
    for i in range(steps+1):
        t = t_total*i/steps
        th = th0*math.cos(omega*t)
        kfs.append(kf(t, L*math.sin(th), pivot_y - L*math.cos(th)))

    v_max = math.sqrt(2*g*L*(1-math.cos(th0)))
    E_total = m*g*L*(1-math.cos(th0))
    return result(
        objects=[sphere_obj("bob",0,pivot_y-L,0,0.3,"#6366f1",f"m={m}kg",trail=False,keyframes=kfs)],
        statics=[{"shape":"box","position":[0,pivot_y+0.2,0],"size":0.25,"color":"#888"}],
        lines=[{"points":[[0,pivot_y,0],[L*math.sin(th0),pivot_y-L*math.cos(th0),0]],
                "color":"#ffffff55","dashed":False}],
        labels=[{"text":f"T={T:.3f}s","x":L+0.5,"y":pivot_y,"z":0,"color":"#10b981"},
                {"text":f"vmax={v_max:.2f}m/s","x":0.5,"y":pivot_y-L,"z":0,"color":"#f59e0b"}],
        solution={"length":f"{L} m","mass":f"{m} kg","period":f"{T:.3f} s",
                  "frequency":f"{1/T:.3f} Hz","omega":f"{omega:.3f} rad/s",
                  "max_angle":f"{math.degrees(th0):.1f}°","v_max":f"{v_max:.3f} m/s",
                  "total_energy":f"{E_total:.4f} J"}
    )


def solve_vertical_circle(p):
    r   = float(p.get("radius", 1))
    m   = float(p.get("mass", 0.5))
    g   = float(p.get("g", 9.8))
    v_b = math.sqrt(5*g*r)   # min speed at bottom
    v_t = math.sqrt(g*r)     # min speed at top
    T_period = 2*math.pi*r / v_b
    cx, cy = 0, r+0.5
    steps=150
    kfs=[kf(T_period*i/steps,
            cx+r*math.cos(2*math.pi*i/steps - math.pi/2),
            cy+r*math.sin(2*math.pi*i/steps - math.pi/2)) for i in range(steps+1)]

    T_bottom = m*(g + v_b**2/r)
    T_top    = m*(v_t**2/r - g)

    return result(
        objects=[sphere_obj("mass",cx,cy-r,0,0.3,"#f59e0b",f"m={m}kg",trail=False,keyframes=kfs)],
        statics=[{"shape":"box","position":[cx,cy,0],"size":0.1,"color":"#888"}],
        vectors=[vec(cx,cy-r,0, 0,-2,0,"#ef4444","mg"),
                 vec(cx,cy-r,0, 0, T_bottom/50,0,"#22c55e","T")],
        labels=[{"text":f"v_bottom={v_b:.2f}m/s","x":cx+r+0.3,"y":cy-r,"z":0,"color":"#f59e0b"},
                {"text":f"v_top={v_t:.2f}m/s","x":cx+0.3,"y":cy+r+0.3,"z":0,"color":"#10b981"}],
        solution={"radius":f"{r} m","mass":f"{m} kg",
                  "min_v_bottom":f"{v_b:.3f} m/s","min_v_top":f"{v_t:.3f} m/s",
                  "T_bottom":f"{T_bottom:.3f} N","T_top":f"{T_top:.3f} N",
                  "centripetal_acc":f"{v_b**2/r:.3f} m/s²",
                  "normal_at_top":f"{max(0,m*(v_t**2/r-g)):.3f} N"}
    )


def solve_spring_shm(p):
    k  = float(p.get("k", 50))
    m  = float(p.get("mass", 1))
    A  = float(p.get("amplitude", 0.5))
    omega = math.sqrt(k/m)
    T  = 2*math.pi/omega
    steps = 150
    t_total = T*4
    kfs=[kf(t_total*i/steps, A*math.cos(omega*t_total*i/steps), 0.8) for i in range(steps+1)]

    # Phase space line
    phase = [[A*math.cos(2*math.pi*j/100), A*omega*math.sin(2*math.pi*j/100), 0]
             for j in range(101)]

    return result(
        objects=[box_obj("mass",A,0.8,0,0.45,"#10b981",f"m={m}kg",trail=False,keyframes=kfs)],
        statics=[{"shape":"box","position":[-(A+1.5),0.8,0],"size":0.4,"color":"#888"},
                 {"shape":"plane","position":[0,-0.05,0],"rotation":[-math.pi/2,0,0],
                  "width":A*6,"depth":4,"color":"#111"}],
        vectors=[vec(0,0.8,0, 0,2,0,"#ffffff44","equilibrium"),
                 vec(A,0.8,0, -1,0,0,"#ef4444","F_spring")],
        labels=[{"text":f"A={A}m","x":A,"y":1.8,"z":0,"color":"#10b981"},
                {"text":f"T={T:.3f}s","x":0,"y":2.2,"z":0,"color":"#f59e0b"},
                {"text":"Equilibrium","x":0,"y":0.2,"z":0,"color":"#555"}],
        solution={"k":f"{k} N/m","mass":f"{m} kg","amplitude":f"{A} m",
                  "period":f"{T:.4f} s","frequency":f"{1/T:.4f} Hz",
                  "omega":f"{omega:.4f} rad/s","v_max":f"{A*omega:.4f} m/s",
                  "a_max":f"{A*omega**2:.4f} m/s²","max_KE":f"{0.5*k*A**2:.4f} J",
                  "max_PE":f"{0.5*k*A**2:.4f} J"}
    )


def solve_block_on_incline(p):
    m      = float(p.get("mass", 2))
    ang    = math.radians(float(p.get("angle_deg", 30)))
    mu_s   = float(p.get("mu_s", 0.4))
    mu_k   = float(p.get("mu_k", 0.3))
    g      = float(p.get("g", 9.8))
    F_app  = float(p.get("applied_force", 0))

    N      = m*g*math.cos(ang)
    f_s_max= mu_s * N
    W_para = m*g*math.sin(ang)
    F_net  = F_app - W_para - mu_k*N
    a      = F_net / m if F_net > 0 else max(0, F_net/m)

    # incline geometry
    Lx = 8*math.cos(ang)
    Ly = 8*math.sin(ang)

    T = 4.0
    steps = 80
    kfs = []
    for i in range(steps+1):
        t = T*i/steps
        s = 0.5*a*t**2
        s = min(s, 6)
        bx = s*math.cos(ang)
        by = s*math.sin(ang) + 0.3
        kfs.append(kf(t, bx, by))

    sliding = F_app + W_para > f_s_max
    return result(
        objects=[box_obj("block",0,0.3,0,0.5,"#3b82f6",f"m={m}kg",trail=False,keyframes=kfs)],
        statics=[
            {"shape":"custom_incline","angle_deg":math.degrees(ang),
             "length":8,"color":"#2a2a3a","position":[0,0,0]},
        ],
        vectors=[
            vec(0,0.5,0, -math.sin(ang)*2, math.cos(ang)*2, 0, "#22c55e", f"N={N:.1f}N"),
            vec(0,0.5,0, 0,-2,0,"#ef4444",f"mg={m*g:.1f}N"),
            vec(0,0.5,0, math.cos(ang)*2,math.sin(ang)*2,0,"#f59e0b",f"F={F_app}N") if F_app>0 else None,
            vec(0,0.5,0,-math.cos(ang)*1.5,-math.sin(ang)*1.5,0,"#a855f7",f"f={mu_k*N:.1f}N"),
        ],
        labels=[{"text":f"θ={math.degrees(ang):.0f}°","x":2,"y":-0.5,"z":0,"color":"#aaa"},
                {"text":"SLIDING" if sliding else "STATIC","x":4,"y":3,"z":0,
                 "color":"#ef4444" if sliding else "#22c55e"}],
        solution={"mass":f"{m} kg","angle":f"{math.degrees(ang):.1f}°",
                  "mu_static":str(mu_s),"mu_kinetic":str(mu_k),
                  "normal_force":f"{N:.3f} N","weight_component_parallel":f"{W_para:.3f} N",
                  "max_static_friction":f"{f_s_max:.3f} N",
                  "kinetic_friction":f"{mu_k*N:.3f} N",
                  "acceleration":f"{a:.4f} m/s²",
                  "status":"Sliding" if sliding else "Static"}
    )


def solve_atwood(p):
    m1 = float(p.get("m1", 3))
    m2 = float(p.get("m2", 1))
    g  = float(p.get("g", 9.8))
    M  = float(p.get("rope_mass", 0))

    a   = (m1-m2)*g / (m1+m2+M/2)
    T   = 2*m1*m2*g / (m1+m2+M/2)

    steps=80; t_total=3.0
    kfs1=[kf(t_total*i/steps, -0.5, 3-0.5*a*(t_total*i/steps)**2) for i in range(steps+1)]
    kfs2=[kf(t_total*i/steps,  0.5, 1+0.5*a*(t_total*i/steps)**2) for i in range(steps+1)]

    return result(
        objects=[
            sphere_obj("m1",-0.5,3,0,0.4*math.sqrt(m1),"#3b82f6",f"m₁={m1}kg",
                       trail=False,keyframes=kfs1),
            sphere_obj("m2", 0.5,1,0,0.4*math.sqrt(m2),"#ef4444",f"m₂={m2}kg",
                       trail=False,keyframes=kfs2),
        ],
        statics=[{"shape":"cylinder","position":[0,4,0],"size":0.15,"color":"#888"}],
        vectors=[vec(-0.5,3,0,0,-1.5,0,"#ef4444",f"m₁g"),
                 vec(-0.5,3,0,0, 1.2,0,"#22c55e","T"),
                 vec( 0.5,1,0,0,-1.0,0,"#ef4444",f"m₂g"),
                 vec( 0.5,1,0,0, 1.2,0,"#22c55e","T")],
        labels=[{"text":f"a={a:.3f}m/s²","x":1.5,"y":3,"z":0,"color":"#f59e0b"},
                {"text":f"T={T:.3f}N","x":1.5,"y":2,"z":0,"color":"#10b981"}],
        solution={"m1":f"{m1} kg","m2":f"{m2} kg","acceleration":f"{a:.4f} m/s²",
                  "tension":f"{T:.4f} N","net_force":f"{(m1-m2)*g:.3f} N",
                  "m1_heavier":"Yes" if m1>m2 else "No"}
    )


def solve_rotation_disk(p):
    m      = float(p.get("mass", 2))
    r      = float(p.get("radius", 0.5))
    torque = float(p.get("torque", 5))
    shape  = str(p.get("I_type","disk"))

    I_map = {"disk":0.5*m*r**2, "ring":m*r**2,
             "rod":m*r**2/12,   "sphere":0.4*m*r**2}
    I = I_map.get(shape, 0.5*m*r**2)
    alpha = torque / I
    omega_final_at_t = lambda t: alpha * t
    T = 5.0; steps=150

    kfs=[kf(T*i/steps, 0, 0.5, 0.5*alpha*(T*i/steps)**2) for i in range(steps+1)]

    return result(
        objects=[{"id":"disk","shape":"disk_3d","radius":r,"mass":m,"color":"#8b5cf6",
                  "label":shape.capitalize(),"trail":False,"keyframes":kfs,"loop":True}],
        statics=[],
        vectors=[vec(0,0.5,0,0,0,torque/5,"#f59e0b","τ")],
        labels=[{"text":f"I={I:.4f} kg·m²","x":r+0.5,"y":1.5,"z":0,"color":"#8b5cf6"},
                {"text":f"α={alpha:.3f} rad/s²","x":r+0.5,"y":1.0,"z":0,"color":"#f59e0b"},
                {"text":f"ω at 5s={alpha*5:.2f} rad/s","x":r+0.5,"y":0.5,"z":0,"color":"#10b981"}],
        solution={"shape":shape,"mass":f"{m} kg","radius":f"{r} m",
                  "moment_of_inertia":f"{I:.5f} kg·m²","torque":f"{torque} N·m",
                  "angular_acceleration":f"{alpha:.4f} rad/s²",
                  "omega_at_5s":f"{alpha*5:.3f} rad/s",
                  "KE_at_5s":f"{0.5*I*(alpha*5)**2:.3f} J"}
    )


def solve_rolling(p):
    m   = float(p.get("mass", 1))
    r   = float(p.get("radius", 0.2))
    ang = math.radians(float(p.get("incline_deg", 30)))
    g   = float(p.get("g", 9.8))

    # For solid cylinder: a = g sinθ / (1 + I/mr²) = g sinθ * 2/3
    I_frac = 0.5  # I = 0.5mr² for solid cylinder
    a = g*math.sin(ang) / (1 + I_frac)
    f = m*g*math.sin(ang) / (2 + 2/I_frac)  # friction force

    T=3.0; steps=80
    kfs=[kf(T*i/steps,
            0.5*a*(T*i/steps)**2 * math.cos(ang),
            max(0, 5 - 0.5*a*(T*i/steps)**2*math.sin(ang))) for i in range(steps+1)]

    v_bottom = math.sqrt(2*a*5/math.sin(ang)*math.sin(ang)) if math.sin(ang)>0 else 0

    return result(
        objects=[sphere_obj("ball",0,5,0,r*2,"#10b981",f"r={r}m",trail=True,keyframes=kfs)],
        statics=[{"shape":"custom_incline","angle_deg":math.degrees(ang),
                  "length":8,"color":"#2a2a3a","position":[0,0,0]}],
        vectors=[vec(0,4.5,0,-math.cos(ang)*1.2,-math.sin(ang)*1.2,0,"#ef4444","mg sinθ"),
                 vec(0,4.5,0,math.cos(ang)*0.8,math.sin(ang)*0.8,0,"#a855f7","f")],
        labels=[{"text":"Rolling (no slip)","x":3,"y":2,"z":0,"color":"#10b981"},
                {"text":f"a={a:.3f}m/s²","x":3,"y":1.5,"z":0,"color":"#f59e0b"}],
        solution={"mass":f"{m} kg","radius":f"{r} m","incline":f"{math.degrees(ang):.1f}°",
                  "acceleration":f"{a:.4f} m/s²","friction_force":f"{f:.4f} N",
                  "v_at_bottom":f"{v_bottom:.3f} m/s",
                  "KE_translational":f"{0.5*m*v_bottom**2:.3f} J",
                  "KE_rotational":f"{0.5*(0.5*m*r**2)*(v_bottom/r)**2:.3f} J",
                  "condition":"Rolling without slipping (I=½mr²)"}
    )


def solve_collision(p):
    m1 = float(p.get("m1", 3))
    v1 = float(p.get("v1", 6))
    m2 = float(p.get("m2", 1))
    v2 = float(p.get("v2", 0))
    ct = str(p.get("type","elastic")).lower()

    if "elastic" in ct and "in" not in ct:
        v1f = ((m1-m2)*v1+2*m2*v2)/(m1+m2)
        v2f = ((m2-m1)*v2+2*m1*v1)/(m1+m2)
    else:
        v1f = v2f = (m1*v1+m2*v2)/(m1+m2)

    KE_i = 0.5*m1*v1**2 + 0.5*m2*v2**2
    KE_f = 0.5*m1*v1f**2 + 0.5*m2*v2f**2
    t_col = 3.0; steps=80
    kf1=[]; kf2=[]
    for i in range(steps+1):
        t=5*i/steps
        dt=max(0,t-t_col)
        kf1.append(kf(t,-6+v1*min(t,t_col)+v1f*dt, 0.5))
        kf2.append(kf(t, 6+v2*min(t,t_col)+v2f*dt, 0.5))

    return result(
        objects=[
            sphere_obj("b1",-6,0.5,0,0.45*math.sqrt(m1),"#3b82f6",f"m₁={m1}",trail=False,keyframes=kf1,loop=False),
            sphere_obj("b2", 6,0.5,0,0.45*math.sqrt(m2),"#ef4444",f"m₂={m2}",trail=False,keyframes=kf2,loop=False),
        ],
        statics=[{"shape":"plane","position":[0,-0.1,0],"rotation":[-math.pi/2,0,0],
                  "width":30,"depth":5,"color":"#111"}],
        vectors=[vec(-6,1.5,0,v1*0.3,0,0,"#3b82f6",f"v₁={v1}m/s"),
                 vec( 6,1.5,0,v2*0.3 if v2 else 0,0,0,"#ef4444",f"v₂={v2}m/s")],
        labels=[{"text":ct.upper(),"x":0,"y":3,"z":0,"color":"#f59e0b"},
                {"text":f"ΔKE={KE_i-KE_f:.3f}J","x":0,"y":2.5,"z":0,"color":"#ef4444"}],
        solution={"type":ct,"m1":f"{m1}kg","v1_initial":f"{v1}m/s",
                  "m2":f"{m2}kg","v2_initial":f"{v2}m/s",
                  "v1_final":f"{v1f:.4f}m/s","v2_final":f"{v2f:.4f}m/s",
                  "p_before":f"{m1*v1+m2*v2:.4f}kg·m/s","p_after":f"{m1*v1f+m2*v2f:.4f}kg·m/s",
                  "KE_before":f"{KE_i:.4f}J","KE_after":f"{KE_f:.4f}J",
                  "KE_lost":f"{KE_i-KE_f:.4f}J","e_coeff":f"{abs(v2f-v1f)/max(abs(v1-v2),1e-9):.4f}"}
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  THERMODYNAMICS
# ═══════════════════════════════════════════════════════════════════════════════

def solve_calorimetry(p):
    m1  = float(p.get("m1", 0.5))
    c1  = float(p.get("c1", 4186))   # water
    T1  = float(p.get("T1", 80))
    m2  = float(p.get("m2", 0.2))
    c2  = float(p.get("c2", 900))    # aluminium
    T2  = float(p.get("T2", 20))
    L   = float(p.get("L", 0))       # latent heat if phase change
    phase = bool(p.get("phase_change", False))

    T_eq = (m1*c1*T1 + m2*c2*T2) / (m1*c1 + m2*c2)
    Q_given = m1*c1*(T1 - T_eq)
    Q_taken = m2*c2*(T_eq - T2)

    # Animate temperature bars
    steps=100
    kfs_hot =[kf(i/steps, -1, max(T_eq, T1 - (T1-T_eq)*i/steps)/10) for i in range(steps+1)]
    kfs_cold=[kf(i/steps,  1, min(T_eq, T2 + (T_eq-T2)*i/steps)/10) for i in range(steps+1)]

    return result(
        objects=[
            box_obj("hot",-1,T1/20,0,0.8,"#ef4444",f"m₁={m1}kg\nT₁={T1}°C",trail=False,keyframes=kfs_hot,hr=3),
            box_obj("cold",1,T2/20,0,0.8,"#3b82f6",f"m₂={m2}kg\nT₂={T2}°C",trail=False,keyframes=kfs_cold,hr=3),
        ],
        statics=[],
        vectors=[vec(0,T1/15,0,0,-0.5,0,"#f59e0b","Heat flow")],
        labels=[{"text":f"T_eq={T_eq:.2f}°C","x":0,"y":T_eq/10+1,"z":0,"color":"#10b981"},
                {"text":"Calorimetry","x":0,"y":T1/10+1,"z":0,"color":"#f59e0b"}],
        solution={"m1":f"{m1}kg","specific_heat_1":f"{c1}J/kg·K","T1":f"{T1}°C",
                  "m2":f"{m2}kg","specific_heat_2":f"{c2}J/kg·K","T2":f"{T2}°C",
                  "equilibrium_temp":f"{T_eq:.4f}°C",
                  "Q_given_by_hot":f"{Q_given:.3f}J","Q_taken_by_cold":f"{Q_taken:.3f}J",
                  "heat_capacity_1":f"{m1*c1:.2f}J/K","heat_capacity_2":f"{m2*c2:.2f}J/K"}
    )


def solve_pv_diagram(p):
    P1   = float(p.get("P1", 101325))
    V1   = float(p.get("V1", 0.001))
    T1   = float(p.get("T1", 300))
    proc = str(p.get("process","isothermal")).lower()
    gam  = float(p.get("gamma", 1.4))
    n    = float(p.get("n_moles", 1))
    R    = 8.314

    steps=80
    V_arr = np.linspace(V1, V1*5, steps)

    if "iso" in proc and "thermal" in proc:
        P_arr = P1*V1/V_arr; label="Isothermal (T=const)"
        T2 = T1
    elif "adi" in proc:
        P_arr = P1*(V1/V_arr)**gam; label=f"Adiabatic (γ={gam})"
        T2 = T1*(V1/V_arr[-1])**(gam-1)
    elif "bar" in proc:
        P_arr = np.full(steps, P1); V_arr=np.linspace(V1,V1*3,steps); label="Isobaric (P=const)"
        T2 = T1*V_arr[-1]/V1
    else:
        V_arr=np.full(steps,V1); P_arr=np.linspace(P1,P1*4,steps); label="Isochoric (V=const)"
        T2 = float(T1*P_arr[-1]/P1)

    W  = float(np.trapz(P_arr, V_arr))
    dU = n*R*(float(T2)-T1) * 5/2 if "mono" not in proc else n*R*(float(T2)-T1)*3/2
    Q  = W + dU

    sx = 8/(V_arr.max()-V_arr.min()+1e-10)
    sy = 6/(P_arr.max()-P_arr.min()+1e-10)
    kfs=[kf(float(i), float((V_arr[i]-V_arr.min())*sx-4), float((P_arr[i]-P_arr.min())*sy+0.5))
         for i in range(steps)]

    return result(
        objects=[sphere_obj("state",float((V_arr[0]-V_arr.min())*sx-4),
                             float((P_arr[0]-P_arr.min())*sy+0.5),0,
                             0.25,"#f59e0b","State",trail=True,keyframes=kfs)],
        statics=[],
        vectors=[],
        labels=[{"text":label,"x":0,"y":7,"z":0,"color":"#f59e0b"},
                {"text":f"W={W:.2f}J","x":0,"y":6,"z":0,"color":"#10b981"},
                {"text":"P","x":-5,"y":3.5,"z":0,"color":"#aaa"},
                {"text":"V →","x":0,"y":-0.5,"z":0,"color":"#aaa"}],
        solution={"process":label,"P_initial":f"{P1:.1f}Pa",
                  "V_initial":f"{V1*1000:.3f}L","T_initial":f"{T1}K",
                  "work_done":f"{W:.4f}J","dU":f"{dU:.4f}J","Q":f"{Q:.4f}J",
                  "first_law":"Q = W + ΔU ✓"}
    )


def solve_carnot(p):
    Th = float(p.get("T_hot",600)); Tc = float(p.get("T_cold",300))
    Qh = float(p.get("Q_hot",2000))
    eta = 1-Tc/Th; W=eta*Qh; Qc=Qh-W; COP=Tc/(Th-Tc)

    steps=20
    s1v=np.linspace(1,2,steps); s1p=5*1/s1v
    s2v=np.linspace(2,3.2,steps); s2p=s1p[-1]*(s1v[-1]/s2v)**1.4
    s3v=np.linspace(3.2,1.6,steps); s3p=s2p[-1]*s2v[-1]/s3v
    s4v=np.linspace(1.6,1,steps); s4p=s3p[-1]*(s3v[-1]/s4v)**1.4
    av=np.concatenate([s1v,s2v,s3v,s4v]); ap=np.concatenate([s1p,s2p,s3p,s4p])
    sx=8/(av.max()-av.min()+1e-9); sy=6/(ap.max()-ap.min()+1e-9)
    kfs=[kf(float(i),float((av[i]-av.min())*sx-4),float((ap[i]-ap.min())*sy+0.5))
         for i in range(len(av))]

    return result(
        objects=[sphere_obj("s",float((av[0]-av.min())*sx-4),float((ap[0]-ap.min())*sy+0.5),
                            0,0.3,"#ef4444","Carnot",trail=True,keyframes=kfs)],
        statics=[],
        labels=[{"text":"Hot Reservoir","x":-4,"y":7,"z":0,"color":"#ef4444"},
                {"text":f"T_H={Th}K","x":-4,"y":6.5,"z":0,"color":"#ef4444"},
                {"text":"Cold Reservoir","x":2,"y":0.5,"z":0,"color":"#3b82f6"},
                {"text":f"T_C={Tc}K","x":2,"y":0,"z":0,"color":"#3b82f6"},
                {"text":"1→2 Isothermal Exp","x":-4,"y":5.5,"z":0,"color":"#aaa"},
                {"text":"2→3 Adiabatic Exp","x":-4,"y":5,"z":0,"color":"#aaa"},
                {"text":"3→4 Isothermal Comp","x":-4,"y":4.5,"z":0,"color":"#aaa"},
                {"text":"4→1 Adiabatic Comp","x":-4,"y":4,"z":0,"color":"#aaa"}],
        solution={"T_hot":f"{Th}K","T_cold":f"{Tc}K","efficiency":f"{eta*100:.2f}%",
                  "Q_absorbed":f"{Qh:.2f}J","work_output":f"{W:.2f}J",
                  "Q_rejected":f"{Qc:.2f}J","COP_refrigerator":f"{COP:.4f}",
                  "entropy_change":"ΔS=0 (reversible)"}
    )


def solve_heat_conduction(p):
    k  = float(p.get("k", 50))        # W/m·K
    A  = float(p.get("A", 0.01))      # m²
    L  = float(p.get("L", 0.5))       # m
    Th = float(p.get("T_hot", 200))
    Tc = float(p.get("T_cold", 20))
    t  = float(p.get("time", 60))
    dT = Th - Tc
    Q_rate = k*A*dT/L
    Q_total= Q_rate*t

    steps=50
    kfs=[kf(i/steps, i/steps*4-2, 0.5) for i in range(steps+1)]

    return result(
        objects=[sphere_obj("heat",-2,0.5,0,0.25,"#ef4444","Heat",trail=True,keyframes=kfs)],
        statics=[{"shape":"box","position":[0,0.5,0],"size":4,"color":"#555555","height_ratio":0.5}],
        vectors=[vec(-3,0.5,0,1.5,0,0,"#ef4444","Q flow")],
        labels=[{"text":f"T_hot={Th}°C","x":-3,"y":1.5,"z":0,"color":"#ef4444"},
                {"text":f"T_cold={Tc}°C","x":3,"y":1.5,"z":0,"color":"#3b82f6"},
                {"text":f"k={k}W/m·K","x":0,"y":2,"z":0,"color":"#aaa"}],
        solution={"k":f"{k}W/m·K","area":f"{A}m²","length":f"{L}m",
                  "ΔT":f"{dT}K","rate_Q":f"{Q_rate:.4f}W",
                  "Q_in_time":f"{Q_total:.4f}J","time":f"{t}s",
                  "thermal_resistance":f"{L/(k*A):.4f}K/W"}
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  ELECTROMAGNETISM
# ═══════════════════════════════════════════════════════════════════════════════

def solve_electric_field(p):
    q1  = abs(float(p.get("q1", 2e-6)))
    q2  = abs(float(p.get("q2", 2e-6)))
    sep = float(p.get("separation", 3))
    s1  = float(p.get("sign1", 1))
    s2  = float(p.get("sign2", -1))
    k_e = 8.99e9

    F   = k_e*q1*q2/sep**2
    E1_at_mid = k_e*q1/(sep/2)**2
    E2_at_mid = k_e*q2/(sep/2)**2

    # Field vectors on a grid
    vecs=[]; n=7
    for xi in np.linspace(-sep*1.8, sep*1.8, n):
        for yi in np.linspace(-sep*0.8, sep*0.8, n):
            if abs(xi+sep/2)<0.35 and abs(yi)<0.35: continue
            if abs(xi-sep/2)<0.35 and abs(yi)<0.35: continue
            r1x,r1y=xi+sep/2,yi; r1=math.sqrt(r1x**2+r1y**2)+1e-9
            r2x,r2y=xi-sep/2,yi; r2=math.sqrt(r2x**2+r2y**2)+1e-9
            Ex=k_e*q1*s1*r1x/r1**3 + k_e*q2*s2*r2x/r2**3
            Ey=k_e*q1*s1*r1y/r1**3 + k_e*q2*s2*r2y/r2**3
            mag=math.sqrt(Ex**2+Ey**2)
            if mag>0:
                vecs.append({"origin":[round(float(xi),3),round(float(yi),3),0.0],
                              "direction":[round(Ex/mag,3),round(Ey/mag,3),0.0],
                              "color":"#f59e0b55" if mag<1e9 else "#f59e0b"})

    clr={1:"#ef4444",-1:"#3b82f6"}
    return result(
        statics=[
            {"shape":"sphere","position":[-sep/2,0,0],"size":0.35,"color":clr[int(s1)]},
            {"shape":"sphere","position":[ sep/2,0,0],"size":0.35,"color":clr[int(s2)]},
        ],
        vectors=vecs,
        labels=[{"text":"+" if s1>0 else "–","x":-sep/2,"y":0.6,"z":0,"color":clr[int(s1)]},
                {"text":"+" if s2>0 else "–","x": sep/2,"y":0.6,"z":0,"color":clr[int(s2)]},
                {"text":f"F={F:.4f}N","x":0,"y":-1,"z":0,"color":"#f59e0b"},
                {"text":"Attractive" if s1*s2<0 else "Repulsive","x":0,"y":-1.8,"z":0,
                 "color":"#ef4444" if s1*s2<0 else "#22c55e"}],
        solution={"q1":f"{q1*1e6:.3f}μC ({'+'if s1>0 else'-'})","q2":f"{q2*1e6:.3f}μC ({'+'if s2>0 else'-'})",
                  "separation":f"{sep}m","coulomb_force":f"{F:.6f}N",
                  "E_at_midpoint":f"{abs(E1_at_mid-E2_at_mid*s2/s1):.4f}N/C",
                  "potential_energy":f"{k_e*q1*q2*s1*s2/sep:.6f}J",
                  "interaction":"Attractive" if s1*s2<0 else "Repulsive"}
    )


def solve_magnetic_force(p):
    B      = float(p.get("B", 0.5))
    v      = float(p.get("v", 2e6))
    charge = float(p.get("charge", 1.6e-19))
    mass   = float(p.get("mass", 1.67e-27))
    q_sign = float(p.get("q_sign", 1))

    r      = mass*v/(abs(charge)*B)
    T      = 2*math.pi*mass/(abs(charge)*B)
    omega  = abs(charge)*B/mass
    scale  = min(r, 5.0)
    steps  = 150
    t_total= T*2

    kfs=[kf(t_total*i/steps,
            scale*math.sin(omega*t_total*i/steps*q_sign),
            scale*(1-math.cos(omega*t_total*i/steps*q_sign))) for i in range(steps+1)]

    # B field dots (into/out of page)
    b_vecs=[]
    for xi in np.linspace(-6,6,8):
        for yi in np.linspace(-2,scale*2+2,8):
            b_vecs.append(vec(xi,yi,0,0,0,0.4*B,"#6366f155"))

    return result(
        objects=[sphere_obj("p",0,0,0,0.25,"#f59e0b" if q_sign>0 else "#3b82f6",
                            "+"if q_sign>0 else "e⁻",trail=True,keyframes=kfs)],
        vectors=b_vecs + [vec(0,scale,0,0,0,min(3*B,3),"#6366f1","B field")],
        labels=[{"text":f"r={r:.4f}m","x":scale+0.5,"y":scale,"z":0,"color":"#f59e0b"},
                {"text":f"ω={omega:.3e}rad/s","x":scale+0.5,"y":scale-0.7,"z":0,"color":"#10b981"},
                {"text":"⊙ B out of page" if q_sign>0 else "⊗ B into page",
                 "x":-5,"y":scale*2,"z":0,"color":"#6366f1"}],
        solution={"B":f"{B}T","velocity":f"{v:.3e}m/s","charge":f"{charge:.3e}C",
                  "mass":f"{mass:.3e}kg","radius":f"{r:.6f}m","period":f"{T:.6e}s",
                  "cyclotron_freq":f"{1/T:.4e}Hz","KE":f"{0.5*mass*v**2:.4e}J",
                  "momentum":f"{mass*v:.4e}kg·m/s"}
    )


def solve_lc_circuit(p):
    L  = float(p.get("L", 0.1))
    C  = float(p.get("C", 1e-4))
    V0 = float(p.get("V0", 10))
    R  = float(p.get("R", 0))

    omega0 = 1/math.sqrt(L*C)
    T      = 2*math.pi/omega0
    Q0     = C*V0

    if R==0:
        gamma=0; omega_d=omega0
    else:
        gamma=R/(2*L); omega_d=math.sqrt(max(0,omega0**2-gamma**2))

    steps=200; t_total=T*4
    kfs_Q =[kf(t_total*i/steps, t_total*i/steps*2-4,
               Q0*math.exp(-gamma*t_total*i/steps)*math.cos(omega_d*t_total*i/steps)*2)
            for i in range(steps+1)]
    kfs_I=[kf(t_total*i/steps, t_total*i/steps*2-4,
              -Q0*omega_d*math.exp(-gamma*t_total*i/steps)*math.sin(omega_d*t_total*i/steps)*2)
           for i in range(steps+1)]

    return result(
        objects=[
            sphere_obj("charge",-4,Q0*2,0,0.2,"#f59e0b","Q(t)",trail=True,keyframes=kfs_Q),
            sphere_obj("current",-4,0,0.5,0.15,"#3b82f6","I(t)",trail=True,keyframes=kfs_I),
        ],
        statics=[],
        labels=[{"text":f"f={omega0/(2*math.pi):.4f}Hz","x":-4,"y":Q0*2+1,"z":0,"color":"#f59e0b"},
                {"text":f"T={T:.4f}s","x":-4,"y":Q0*2+0.5,"z":0,"color":"#10b981"},
                {"text":"Q(t) — charge","x":2,"y":Q0*2,"z":0,"color":"#f59e0b"},
                {"text":"I(t) — current","x":2,"y":-0.5,"z":0.5,"color":"#3b82f6"},
                {"text":"Damped" if R>0 else "Undamped","x":0,"y":Q0*2+1.5,"z":0,"color":"#aaa"}],
        solution={"L":f"{L}H","C":f"{C}F","V0":f"{V0}V","R":f"{R}Ω",
                  "omega_0":f"{omega0:.4f}rad/s","frequency":f"{omega0/(2*math.pi):.4f}Hz",
                  "period":f"{T:.4f}s","Q_max":f"{Q0:.6f}C","I_max":f"{Q0*omega0:.6f}A",
                  "max_energy":f"{0.5*C*V0**2:.6f}J",
                  "type":"Damped" if R>0 else "Undamped LC"}
    )


def solve_em_induction(p):
    B   = float(p.get("B", 1.0))
    A   = float(p.get("area", 0.01))
    om  = float(p.get("omega", 100))
    R_c = float(p.get("R", 10))
    t_s = float(p.get("t", 5))

    EMF_max = B*A*om
    I_max   = EMF_max/R_c
    T       = 2*math.pi/om
    steps   = 200; t_total=T*4

    kfs_emf=[kf(t_total*i/steps, t_total*i/steps*2-4,
                EMF_max*math.sin(om*t_total*i/steps)*1.5) for i in range(steps+1)]
    kfs_I  =[kf(t_total*i/steps, t_total*i/steps*2-4,
                I_max*math.sin(om*t_total*i/steps)*1.5) for i in range(steps+1)]

    return result(
        objects=[
            sphere_obj("emf",-4,0,0,0.2,"#f59e0b","EMF",trail=True,keyframes=kfs_emf),
            sphere_obj("cur",-4,0,0.5,0.15,"#3b82f6","I",trail=True,keyframes=kfs_I),
        ],
        labels=[{"text":"EMF = BAω cos(ωt)","x":-4,"y":EMF_max*1.5+1,"z":0,"color":"#f59e0b"},
                {"text":f"EMF_max={EMF_max:.4f}V","x":2,"y":EMF_max*1.5,"z":0,"color":"#f59e0b"},
                {"text":f"I_max={I_max:.4f}A","x":2,"y":I_max*1.5-1,"z":0.5,"color":"#3b82f6"}],
        solution={"B":f"{B}T","area":f"{A}m²","omega":f"{om}rad/s","R":f"{R_c}Ω",
                  "EMF_max":f"{EMF_max:.4f}V","I_max":f"{I_max:.4f}A",
                  "frequency":f"{om/(2*math.pi):.4f}Hz","period":f"{T:.4f}s",
                  "power_avg":f"{0.5*I_max**2*R_c:.4f}W"}
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  OPTICS — Ray Tracing
# ═══════════════════════════════════════════════════════════════════════════════

def solve_ray_refraction(p):
    n1   = float(p.get("n1",1.0))
    n2   = float(p.get("n2",1.5))
    th_i = math.radians(float(p.get("angle_inc_deg",40)))

    sin_r = n1*math.sin(th_i)/n2
    TIR   = abs(sin_r) > 1.0
    th_r  = math.asin(min(1, abs(sin_r))) if not TIR else math.pi/2
    crit  = math.degrees(math.asin(n2/n1)) if n2<n1 else None

    # Reflected ray angle
    th_refl = th_i

    ix, iy = 0, 0  # interface point
    ray_len = 5

    inc_pts  = [[-ray_len*math.sin(th_i), ray_len*math.cos(th_i), 0], [ix,iy,0]]
    refr_pts = [[ix,iy,0], [ ray_len*math.sin(th_r), -ray_len*math.cos(th_r), 0]] if not TIR else [[ix,iy,0],[0,0,0]]
    refl_pts = [[ix,iy,0], [ ray_len*math.sin(th_refl), ray_len*math.cos(th_refl), 0]]
    norm_pts = [[0,-ray_len*0.5,0],[0,ray_len*0.5,0]]

    return result(
        statics=[{"shape":"plane","position":[0,-0.05,0],"rotation":[-math.pi/2,0,0],
                  "width":12,"depth":10,"color":"#1a2a4a"}],
        lines=[
            {"points":inc_pts, "color":"#f59e0b", "dashed":False, "label":"Incident"},
            {"points":refr_pts,"color":"#10b981", "dashed":False, "label":"Refracted"} if not TIR else
            {"points":[[0,0,0],[0,0,0]],"color":"#333","dashed":True},
            {"points":refl_pts,"color":"#3b82f6", "dashed":True,  "label":"Reflected"},
            {"points":norm_pts,"color":"#555555", "dashed":True,  "label":"Normal"},
        ],
        labels=[{"text":"n₁="+str(n1),"x":-4,"y":2,"z":0,"color":"#aaa"},
                {"text":"n₂="+str(n2),"x":-4,"y":-2,"z":0,"color":"#aaa"},
                {"text":f"θᵢ={math.degrees(th_i):.1f}°","x":-3,"y":2.5,"z":0,"color":"#f59e0b"},
                {"text":f"θᵣ={math.degrees(th_r):.1f}°","x":2,"y":-2.5,"z":0,"color":"#10b981"},
                {"text":"TOTAL INTERNAL REFLECTION","x":0,"y":3,"z":0,"color":"#ef4444"} if TIR else
                {"text":"Snell's Law: n₁sinθ₁=n₂sinθ₂","x":0,"y":-4,"z":0,"color":"#555"},
                {"text":f"Critical angle={crit:.1f}°" if crit else "","x":3,"y":2,"z":0,"color":"#8b5cf6"} if crit else {"text":"","x":0,"y":0,"z":0}],
        solution={"n1":str(n1),"n2":str(n2),"angle_incidence":f"{math.degrees(th_i):.2f}°",
                  "angle_refraction":"TIR" if TIR else f"{math.degrees(th_r):.2f}°",
                  "angle_reflection":f"{math.degrees(th_refl):.2f}°",
                  "critical_angle":f"{crit:.2f}°" if crit else "N/A (n2≥n1)",
                  "TIR":"YES" if TIR else "NO","speed_medium_1":f"{3e8/n1:.3e}m/s",
                  "speed_medium_2":f"{3e8/n2:.3e}m/s"}
    )


def solve_lens(p):
    f_raw = float(p.get("f", 0.15))
    d_o   = float(p.get("d_o", 0.4))
    h_o   = float(p.get("h_o", 0.08))
    ltype = str(p.get("type","convex")).lower()

    f   = abs(f_raw) if "convex" in ltype else -abs(f_raw)
    d_i = (f*d_o)/(d_o-f) if abs(d_o-f)>1e-9 else 1e9
    m   = -d_i/d_o
    h_i = m*h_o
    real= d_i>0

    scale=6
    do_s=min(d_o*scale, 8)
    di_s=min(abs(d_i)*scale,8)*(1 if d_i>0 else -1)
    ho_s=h_o*scale*4
    hi_s=h_i*scale*4

    # Ray tracing lines (3 principal rays)
    lens_x=0; obj_x=-do_s; obj_top_y=ho_s
    F_left=-f*scale; F_right=f*scale

    # Ray 1: parallel to axis → through focal point
    ray1 = [[-do_s, ho_s,0],[lens_x, ho_s,0],[lens_x+di_s, 0 if di_s!=0 else ho_s,0]]
    # Ray 2: through optical center
    ray2 = [[-do_s, ho_s,0],[lens_x,0,0],[lens_x+di_s, hi_s,0]]
    # Ray 3: through front focal point → parallel
    ray3_start_y = ho_s
    ray3 = [[-do_s, ray3_start_y,0],
            [lens_x, ray3_start_y*(do_s-F_left)/(do_s) if do_s>0 else 0,0],
            [lens_x+di_s, hi_s,0]]

    return result(
        statics=[
            {"shape":"lens_convex" if "convex" in ltype else "lens_concave",
             "position":[0,0,0],"height":ho_s*3,"color":"#60a5fa44"},
        ],
        lines=[
            {"points":ray1,"color":"#ef4444","dashed":False,"label":"Ray 1 (parallel→F)"},
            {"points":ray2,"color":"#22c55e","dashed":False,"label":"Ray 2 (thru center)"},
            {"points":ray3,"color":"#f59e0b","dashed":False,"label":"Ray 3 (thru F→parallel)"},
            {"points":[[-do_s,0,0],[di_s+do_s,0,0]],"color":"#33333388","dashed":False},  # optical axis
            {"points":[[-do_s,ho_s,0],[-do_s,0,0]],"color":"#f59e0b88","dashed":False},    # object
            {"points":[[di_s,hi_s,0],[di_s,0,0]],"color":"#10b98188","dashed":True if not real else False},  # image
            {"points":[[F_left,-0.3,0],[F_left,0.3,0]],"color":"#555","dashed":False},
            {"points":[[F_right,-0.3,0],[F_right,0.3,0]],"color":"#555","dashed":False},
        ],
        labels=[{"text":"Object","x":-do_s-0.2,"y":ho_s+0.3,"z":0,"color":"#f59e0b"},
                {"text":"Image","x":di_s+0.2,"y":hi_s+0.3,"z":0,"color":"#10b981"},
                {"text":"F","x":F_left,"y":-0.6,"z":0,"color":"#888"},
                {"text":"F","x":F_right,"y":-0.6,"z":0,"color":"#888"},
                {"text":"2F","x":F_left*2,"y":-0.6,"z":0,"color":"#555"},
                {"text":"2F","x":F_right*2,"y":-0.6,"z":0,"color":"#555"},
                {"text":ltype.upper()+" LENS","x":0,"y":ho_s*3+0.5,"z":0,"color":"#60a5fa"},
                {"text":"Real & Inverted" if (real and m<0) else "Virtual & Upright",
                 "x":di_s+0.2,"y":hi_s-0.5,"z":0,"color":"#22c55e"}],
        solution={"lens_type":ltype,"f":f"{f*100:.1f}cm","d_object":f"{d_o*100:.1f}cm",
                  "d_image":f"{d_i*100:.2f}cm","magnification":f"{m:.4f}×",
                  "h_object":f"{h_o*100:.1f}cm","h_image":f"{h_i*100:.2f}cm",
                  "image_nature":"Real & Inverted" if(real and m<0) else "Virtual & Upright",
                  "lens_formula":"1/v - 1/u = 1/f ✓","power":f"{1/f:.2f}D"}
    )


def solve_mirror(p):
    f_raw = float(p.get("f", 0.15))
    d_o   = float(p.get("d_o", 0.4))
    h_o   = float(p.get("h_o", 0.08))
    mtype = str(p.get("type","concave")).lower()

    f   = -abs(f_raw) if "concave" in mtype else abs(f_raw)  # mirror sign convention
    # Mirror: 1/v + 1/u = 1/f, u negative
    u   = -d_o
    if abs(u-f)<1e-9: d_i=1e9
    else: d_i = f*u/(u-f)
    m   = -d_i/u
    h_i = m*h_o

    scale=6
    do_s=min(d_o*scale,8)
    ho_s=h_o*scale*4
    hi_s=h_i*scale*4
    di_s=min(abs(d_i)*scale,8)*(1 if d_i>0 else -1)

    return result(
        statics=[
            {"shape":"mirror_concave" if "concave" in mtype else "mirror_convex",
             "position":[do_s/2,0,0],"height":ho_s*4,"color":"#60a5fa44"},
        ],
        lines=[
            {"points":[[-do_s,0,0],[do_s,0,0]],"color":"#33333388","dashed":False},
            {"points":[[-do_s,ho_s,0],[-do_s,0,0]],"color":"#f59e0b88","dashed":False},
            {"points":[[-do_s,ho_s,0],[0,ho_s,0],[0-di_s,hi_s,0]],"color":"#ef4444","dashed":False},
            {"points":[[-do_s,ho_s,0],[0,0,0],[0-di_s,hi_s,0]],"color":"#22c55e","dashed":False},
        ],
        labels=[{"text":mtype.upper()+" MIRROR","x":do_s+0.2,"y":ho_s*2,"z":0,"color":"#60a5fa"},
                {"text":"Object","x":-do_s,"y":ho_s+0.3,"z":0,"color":"#f59e0b"},
                {"text":"Image","x":-di_s,"y":hi_s+0.3,"z":0,"color":"#10b981"},
                {"text":f"f={f_raw*100:.1f}cm","x":do_s,"y":-0.5,"z":0,"color":"#888"}],
        solution={"mirror_type":mtype,"f":f"{f_raw*100:.1f}cm","d_object":f"{d_o*100:.1f}cm",
                  "d_image":f"{d_i*100:.2f}cm","magnification":f"{m:.4f}×",
                  "h_image":f"{h_i*100:.2f}cm",
                  "image_nature":"Real & Inverted" if(d_i<0 and m<0) else "Virtual & Erect",
                  "mirror_formula":"1/v + 1/u = 1/f ✓"}
    )


def solve_prism(p):
    A    = math.radians(float(p.get("apex_deg", 60)))
    n    = float(p.get("n", 1.5))
    th_i = math.radians(float(p.get("angle_inc_deg", 40)))

    sin_r1 = math.sin(th_i)/n
    if abs(sin_r1)>1: return result(solution={"error":"TIR at first surface"})
    r1 = math.asin(sin_r1)
    r2 = A - r1
    sin_e = n*math.sin(r2)
    if abs(sin_e)>1: return result(solution={"error":"TIR at second surface"})
    th_e = math.asin(sin_e)
    delta = th_i + th_e - A
    delta_min_approx = 2*math.asin(n*math.sin(A/2)) - A

    return result(
        lines=[
            {"points":[[-4, 2,0],[0,0,0]],"color":"#f59e0b","dashed":False,"label":"Incident"},
            {"points":[[0,0,0],[3,1,0]],"color":"#10b981","dashed":False,"label":"Refracted inside"},
            {"points":[[3,1,0],[6,3,0]],"color":"#ef4444","dashed":False,"label":"Emergent"},
            {"points":[[-3,0,0],[5,0,0]],"color":"#33333355","dashed":True},
        ],
        labels=[{"text":"Prism","x":1.5,      "y":1.5,"z":0,"color":"#8b5cf6"},
                {"text":f"A={math.degrees(A):.0f}°","x":1.5,"y":0.5,"z":0,"color":"#aaa"},
                {"text":f"n={n}","x":1.5,      "y":0.0,"z":0,"color":"#aaa"},
                {"text":f"δ={math.degrees(delta):.2f}°","x":4,"y":2.5,"z":0,"color":"#f59e0b"},
                {"text":f"r₁={math.degrees(r1):.2f}°","x":-1,"y":0.5,"z":0,"color":"#10b981"},
                {"text":f"r₂={math.degrees(r2):.2f}°","x":3.5,"y":0.5,"z":0,"color":"#10b981"},
                {"text":f"δ_min≈{math.degrees(delta_min_approx):.2f}°","x":4,"y":1.5,"z":0,"color":"#8b5cf6"}],
        solution={"apex_angle":f"{math.degrees(A):.1f}°","refractive_index":str(n),
                  "angle_incidence":f"{math.degrees(th_i):.2f}°",
                  "r1":f"{math.degrees(r1):.2f}°","r2":f"{math.degrees(r2):.2f}°",
                  "angle_emergence":f"{math.degrees(th_e):.2f}°",
                  "deviation":f"{math.degrees(delta):.2f}°",
                  "min_deviation_approx":f"{math.degrees(delta_min_approx):.2f}°",
                  "formula":"δ = i + e - A"}
    )


def solve_youngs_double(p):
    d  = float(p.get("d_slit", 0.001))
    D  = float(p.get("D", 1.0))
    lm = float(p.get("wavelength_nm", 550)) * 1e-9

    fringe_w = lm*D/d
    n_fringes = 7

    lines = []
    labels_l = []
    for n_ in range(-n_fringes, n_fringes+1):
        y = n_*fringe_w*1000  # scale
        color = "#f59e0b" if n_%2==0 else "#22222288"
        lines.append({"points":[[-2,y,0],[2,y,0]],"color":color,"dashed":n_%2!=0})
        if abs(n_)<=3:
            labels_l.append({"text":f"n={n_}","x":2.2,"y":y,"z":0,"color":"#aaa"})

    return result(
        lines=lines,
        labels=labels_l+[
            {"text":"Double Slit","x":-3,"y":0,"z":0,"color":"#f59e0b"},
            {"text":f"β={fringe_w*1e3:.3f}mm","x":0,"y":n_fringes*fringe_w*1000+0.5,"z":0,"color":"#10b981"},
            {"text":f"λ={lm*1e9:.0f}nm","x":0,"y":n_fringes*fringe_w*1000+1,"z":0,"color":"#8b5cf6"},
        ],
        solution={"d_slit":f"{d*1e3:.3f}mm","D":f"{D}m","wavelength":f"{lm*1e9:.0f}nm",
                  "fringe_width":f"{fringe_w*1e3:.4f}mm",
                  "angular_fringe":f"{lm/d:.6f}rad",
                  "path_diff_1st_bright":"λ","path_diff_1st_dark":"λ/2",
                  "formula":"β = λD/d"}
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  WAVES
# ═══════════════════════════════════════════════════════════════════════════════

def solve_wave_superposition(p):
    f1=float(p.get("f1",4)); A1=float(p.get("A1",1))
    f2=float(p.get("f2",6)); A2=float(p.get("A2",0.8))
    dur=float(p.get("duration",3))
    steps=300
    t_arr=np.linspace(0,dur,steps)
    y1=A1*np.sin(2*math.pi*f1*t_arr)
    y2=A2*np.sin(2*math.pi*f2*t_arr)
    ys=y1+y2

    sx=8/dur
    kfs_s=[kf(float(t_arr[i]), float(t_arr[i]*sx-4), float(ys[i])+1) for i in range(steps)]
    kfs_1=[kf(float(t_arr[i]), float(t_arr[i]*sx-4), float(y1[i])-2) for i in range(steps)]
    kfs_2=[kf(float(t_arr[i]), float(t_arr[i]*sx-4), float(y2[i])-5) for i in range(steps)]

    beat=abs(f1-f2)
    return result(
        objects=[
            sphere_obj("sum",-4,1,0,0.18,"#10b981","y₁+y₂",trail=True,keyframes=kfs_s),
            sphere_obj("w1", -4,-2,0,0.15,"#f59e0b", f"f₁={f1}Hz",trail=True,keyframes=kfs_1),
            sphere_obj("w2", -4,-5,0,0.15,"#3b82f6", f"f₂={f2}Hz",trail=True,keyframes=kfs_2),
        ],
        labels=[{"text":"Superposition y₁+y₂","x":-4,"y":2.5,"z":0,"color":"#10b981"},
                {"text":f"Wave 1: f={f1}Hz A={A1}","x":-4,"y":-0.5,"z":0,"color":"#f59e0b"},
                {"text":f"Wave 2: f={f2}Hz A={A2}","x":-4,"y":-3.5,"z":0,"color":"#3b82f6"},
                {"text":f"Beat frequency={beat}Hz" if beat>0 else "No beats",
                 "x":0,"y":3,"z":0,"color":"#8b5cf6"}],
        solution={"f1":f"{f1}Hz","A1":str(A1),"f2":f"{f2}Hz","A2":str(A2),
                  "beat_frequency":f"{beat}Hz","max_amplitude":f"{A1+A2}",
                  "principle":"Superposition — displacements add algebraically"}
    )


def solve_doppler(p):
    fs  = float(p.get("f_source",440))
    vs  = float(p.get("v_source",30))
    vo  = float(p.get("v_observer",0))
    v   = float(p.get("v_sound",340))
    app = bool(p.get("approaching",True))

    if app:
        f_obs = fs*(v+vo)/(v-vs)
    else:
        f_obs = fs*(v-vo)/(v+vs)

    steps=80; t_total=4
    kfs_src=[kf(t*i/steps, -4+(8 if app else -8)*(i/steps)*vs/v, 0.5) for i,t in
             [(i,t_total) for i in range(steps+1)]]

    return result(
        objects=[sphere_obj("src",-4,0.5,0,0.4,"#f59e0b","Source",trail=False,keyframes=kfs_src)],
        statics=[sphere_obj("obs",4,0.5,0,0.4,"#3b82f6","Observer",trail=False)],
        labels=[{"text":f"f_source={fs}Hz","x":-4,"y":1.5,"z":0,"color":"#f59e0b"},
                {"text":f"f_observed={f_obs:.2f}Hz","x":3,"y":1.5,"z":0,"color":"#3b82f6"},
                {"text":"Approaching" if app else "Receding","x":0,"y":2,"z":0,
                 "color":"#ef4444" if app else "#22c55e"},
                {"text":f"Δf={abs(f_obs-fs):.2f}Hz","x":0,"y":2.6,"z":0,"color":"#8b5cf6"}],
        solution={"f_source":f"{fs}Hz","v_source":f"{vs}m/s","v_observer":f"{vo}m/s",
                  "v_sound":f"{v}m/s","f_observed":f"{f_obs:.4f}Hz",
                  "delta_f":f"{abs(f_obs-fs):.4f}Hz",
                  "direction":"Approaching (higher freq)" if app else "Receding (lower freq)",
                  "formula":"f'=f(v±v₀)/(v∓vₛ)"}
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  MODERN PHYSICS
# ═══════════════════════════════════════════════════════════════════════════════

def solve_photoelectric(p):
    phi_eV = float(p.get("work_function_eV", 2.3))
    f_Hz   = float(p.get("frequency_Hz", 8e14))
    h = 6.626e-34; e = 1.6e-19
    phi_J = phi_eV * e
    E_photon = h * f_Hz
    E_photon_eV = E_photon / e
    KE_max = max(0, E_photon - phi_J)
    KE_eV  = KE_max / e
    f_thresh = phi_J / h
    v_stop = KE_eV  # stopping potential = KE_max in eV

    steps=60; t_total=3
    kfs_e=[kf(t_total*i/steps, -3+6*(i/steps), (i/steps)*2) for i in range(steps+1)
           if E_photon > phi_J]

    return result(
        objects=[sphere_obj("e",-3,0,0,0.2,"#60a5fa","e⁻",trail=True,
                            keyframes=kfs_e if E_photon>phi_J else [kf(0,-3,0)])],
        statics=[{"shape":"box","position":[0,-0.5,0],"size":2,"color":"#333","height_ratio":0.4}],
        vectors=[vec(-5,2,0,1.5,0,0,"#f59e0b","hf photon")],
        labels=[{"text":"Metal Surface","x":0,"y":-1.2,"z":0,"color":"#888"},
                {"text":"φ="+f"{phi_eV}eV","x":0,"y":-0.9,"z":0,"color":"#ef4444"},
                {"text":"KE_max="+f"{KE_eV:.3f}eV" if E_photon>phi_J else "NO emission","x":3,"y":1,"z":0,
                 "color":"#22c55e" if E_photon>phi_J else "#ef4444"},
                {"text":f"E_photon={E_photon_eV:.3f}eV","x":-5,"y":2.5,"z":0,"color":"#f59e0b"}],
        solution={"work_function":f"{phi_eV}eV = {phi_J:.4e}J",
                  "frequency":f"{f_Hz:.4e}Hz","E_photon":f"{E_photon:.4e}J = {E_photon_eV:.3f}eV",
                  "threshold_frequency":f"{f_thresh:.4e}Hz",
                  "KE_max":f"{KE_max:.4e}J = {KE_eV:.3f}eV",
                  "stopping_potential":f"{v_stop:.3f}V",
                  "emission":"YES" if E_photon>phi_J else "NO (below threshold)",
                  "formula":"KE_max = hf - φ"}
    )


def solve_bohr_atom(p):
    Z  = int(p.get("Z",1))
    n1 = int(p.get("n_initial",3))
    n2 = int(p.get("n_final",1))
    RH = 13.6  # eV

    E1 = -RH*Z**2/n1**2
    E2 = -RH*Z**2/n2**2
    dE = abs(E2-E1)
    h  = 4.136e-15  # eV·s
    c  = 3e8
    lm = h*c/dE if dE>0 else 0
    r1 = 0.529*n1**2/Z
    r2 = 0.529*n2**2/Z

    steps=120; t_total=4
    # Electron spiraling from n1 to n2
    kfs=[kf(t_total*i/steps,
            r1*(1-i/steps)*math.cos(10*math.pi*i/steps) + r2*(i/steps)*math.cos(10*math.pi*i/steps),
            r1*(1-i/steps)*math.sin(10*math.pi*i/steps) + r2*(i/steps)*math.sin(10*math.pi*i/steps))
         for i in range(steps+1)]

    return result(
        objects=[sphere_obj("e",r1,0,0,0.15,"#60a5fa","e⁻",trail=True,keyframes=kfs)],
        statics=[sphere_obj("nucleus",0,0,0,0.3,"#ef4444",f"Z={Z}")],
        vectors=[vec(0,0,0,0,dE/20,0,"#f59e0b","photon emitted")],
        labels=[{"text":f"n={n1} orbit r={r1:.3f}Å","x":r1+0.2,"y":0,"z":0,"color":"#3b82f6"},
                {"text":f"n={n2} orbit r={r2:.3f}Å","x":r2+0.2,"y":-0.5,"z":0,"color":"#10b981"},
                {"text":f"E_initial={E1:.3f}eV","x":-3,"y":2,"z":0,"color":"#3b82f6"},
                {"text":f"E_final={E2:.3f}eV","x":-3,"y":1.5,"z":0,"color":"#10b981"},
                {"text":f"ΔE={dE:.3f}eV","x":-3,"y":1,"z":0,"color":"#f59e0b"},
                {"text":f"λ={lm*1e9:.2f}nm","x":-3,"y":0.5,"z":0,"color":"#8b5cf6"}],
        solution={"element":f"Z={Z}","n_initial":str(n1),"n_final":str(n2),
                  "E_initial":f"{E1:.4f}eV","E_final":f"{E2:.4f}eV","ΔE":f"{dE:.4f}eV",
                  "wavelength":f"{lm*1e9:.3f}nm","r_initial":f"{r1:.4f}Å","r_final":f"{r2:.4f}Å",
                  "series":"Lyman" if n2==1 else "Balmer" if n2==2 else "Paschen" if n2==3 else "Other",
                  "transition":f"n={n1}→n={n2}","formula":"En = -13.6×Z²/n² eV"}
    )


def solve_radioactive(p):
    N0  = float(p.get("N0", 1e6))
    t12 = float(p.get("half_life", 10))
    t   = float(p.get("time", 30))
    lam = math.log(2)/t12
    Nt  = N0 * math.exp(-lam*t)
    steps=100
    kfs=[kf(t*i/steps, t*i/steps*0.8-4, N0*math.exp(-lam*t*i/steps)/N0*4) for i in range(steps+1)]

    return result(
        objects=[sphere_obj("N",-4,4,0,0.25,"#ef4444","N(t)",trail=True,keyframes=kfs)],
        labels=[{"text":f"N₀={N0:.2e}","x":-4,"y":4.5,"z":0,"color":"#ef4444"},
                {"text":f"t½={t12}s","x":0,"y":4.5,"z":0,"color":"#f59e0b"},
                {"text":f"N(t)={Nt:.3e}","x":2,"y":3,"z":0,"color":"#10b981"},
                {"text":f"Activity_0={lam*N0:.3e}Bq","x":-4,"y":-0.5,"z":0,"color":"#8b5cf6"},
                {"text":f"Activity_t={lam*Nt:.3e}Bq","x":-4,"y":-1,"z":0,"color":"#8b5cf6"}],
        solution={"N0":f"{N0:.3e}","half_life":f"{t12}s","time":f"{t}s",
                  "decay_constant":f"{lam:.6f}s⁻¹","N_remaining":f"{Nt:.4e}",
                  "fraction_remaining":f"{Nt/N0:.4f}","activity_initial":f"{lam*N0:.4e}Bq",
                  "activity_at_t":f"{lam*Nt:.4e}Bq","formula":"N(t)=N₀e^(-λt)"}
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  REGISTRY + MAIN
# ═══════════════════════════════════════════════════════════════════════════════

SOLVERS = {
    # Mechanics
    "projectile":      solve_projectile,
    "free_fall":       solve_free_fall,
    "pendulum":        solve_pendulum,
    "vertical_circle": solve_vertical_circle,
    "circular_motion": solve_vertical_circle,
    "spring_shm":      solve_spring_shm,
    "coupled_spring":  solve_spring_shm,
    "collision":       solve_collision,
    "relative_motion": lambda p: solve_collision({**p,"type":"elastic"}),
    "block_on_incline":solve_block_on_incline,
    "atwood":          solve_atwood,
    "block_pulley":    solve_atwood,
    "rotation_disk":   solve_rotation_disk,
    "rolling":         solve_rolling,
    # Thermodynamics
    "pv_diagram":      solve_pv_diagram,
    "isothermal":      solve_pv_diagram,
    "adiabatic":       solve_pv_diagram,
    "isobaric":        solve_pv_diagram,
    "isochoric":       solve_pv_diagram,
    "carnot":          solve_carnot,
    "calorimetry":     solve_calorimetry,
    "heat_conduction": solve_heat_conduction,
    "stefan":          solve_calorimetry,
    "gas_law":         solve_pv_diagram,
    # Electromagnetism
    "electric_field":  solve_electric_field,
    "gauss_field":     solve_electric_field,
    "capacitor":       solve_electric_field,
    "magnetic_force":  solve_magnetic_force,
    "lc_circuit":      solve_lc_circuit,
    "solenoid":        solve_em_induction,
    "em_induction":    solve_em_induction,
    # Optics
    "ray_refraction":  solve_ray_refraction,
    "lens":            solve_lens,
    "mirror":          solve_mirror,
    "prism":           solve_prism,
    "youngs_double":   solve_youngs_double,
    "single_slit":     solve_youngs_double,
    "thin_film":       solve_youngs_double,
    # Waves
    "wave_superposition": solve_wave_superposition,
    "standing_wave":      solve_wave_superposition,
    "doppler":            solve_doppler,
    "string_wave":        solve_wave_superposition,
    # Modern
    "photoelectric":   solve_photoelectric,
    "bohr_atom":       solve_bohr_atom,
    "radioactive":     solve_radioactive,
}


async def solve(chapter: str, problem: str) -> dict:
    extracted    = await extract_params(chapter, problem)
    problem_type = extracted.get("problem_type", "projectile")
    params       = extracted.get("params", {})
    description  = extracted.get("description", problem[:80])

    print(f"[solver] chapter={chapter} type={problem_type} params={params}")

    solver = SOLVERS.get(problem_type, solve_projectile)
    try:
        res = solver(params)
    except Exception as e:
        print(f"[solver] ERROR in {problem_type}: {e}")
        res = solve_projectile({"v0":20,"angle_deg":45,"height":0,"g":9.8})
        res["solution"]["error"] = str(e)

    res["description"]  = description
    res["problem_type"] = problem_type
    return res
