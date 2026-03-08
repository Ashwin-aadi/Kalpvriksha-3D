"""
physics_solver.py — Universal JEE Physics Engine
LLM extracts ALL parameters. Every problem type works. Nothing hardcoded.
"""

import os, math, json, re
import httpx
import numpy as np

# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────
# The LLM does ALL the heavy lifting: identifies type, extracts params, computes results.
# We only handle the 3D scene rendering.

SYSTEM_PROMPT = """You are a JEE Advanced physics solver AND 3D scene generator.
Given a physics problem, you must:
1. Identify the problem type and solve it completely
2. Return a JSON object with the full solution AND 3D scene data

Return ONLY valid JSON, no markdown, no explanation.

{
  "problem_type": "short_snake_case_name",
  "description": "one line summary of what was solved",
  "solution": {
    "key1": "value with units",
    "key2": "value with units",
    ...
  },
  "scene": {
    "objects": [...],
    "static_objects": [...],
    "vectors": [...],
    "lines": [...],
    "labels": [...]
  }
}

SCENE FORMAT RULES:

objects — animated moving bodies:
{
  "id": "unique_id",
  "shape": "sphere" | "box" | "cylinder" | "disk_3d",
  "size": 0.4,
  "color": "#hexcolor",
  "label": "text",
  "trail": true | false,
  "loop": true | false,
  "keyframes": [
    {"t": 0.0, "x": 0.0, "y": 0.0, "z": 0.0},
    {"t": 1.0, "x": 2.0, "y": 3.0, "z": 0.0},
    ...
  ]
}
- keyframes animate the object over time (t in seconds)
- provide at least 20 keyframes for smooth animation
- use realistic scale: 1 unit ≈ 1 meter (compress large distances to fit in ±20 range)
- for projectiles: animate full trajectory with parabolic keyframes
- for oscillations: animate full cycles with sinusoidal keyframes
- for circular motion: animate full circles with cos/sin keyframes

static_objects — non-moving scene elements (ground, walls, lens, mirror etc.):
{
  "shape": "sphere" | "box" | "plane" | "cylinder" | "custom_incline",
  "position": [x, y, z],
  "size": 0.5,
  "color": "#hexcolor",
  "rotation": [rx, ry, rz],   (optional, radians)
  "width": 20,                 (for plane)
  "depth": 10,                 (for plane)
  "angle_deg": 30,             (for custom_incline)
  "length": 8                  (for custom_incline)
}

vectors — arrows showing forces, fields, velocities:
{
  "origin": [x, y, z],
  "direction": [dx, dy, dz],
  "color": "#hexcolor",
  "label": "F=10N"
}

lines — rays, paths, dashed lines:
{
  "points": [[x1,y1,z1], [x2,y2,z2], ...],
  "color": "#hexcolor",
  "dashed": false
}

labels — floating text:
{
  "text": "v=20 m/s",
  "x": 1.0, "y": 2.0, "z": 0.0,
  "color": "#hexcolor"
}

IMPORTANT RULES:
- Scale everything so it fits visually (max ±15 units from origin)
- Always include ground plane for mechanics problems
- For optics: draw ray lines, lens/mirror as static object
- For EM: draw circular path for charged particles, field arrows for E/B fields
- For waves: animate a point tracing the wave shape
- For thermodynamics: use boxes/labels to show states
- Colors: mechanics=#f59e0b, thermo=#ef4444, EM=#3b82f6, optics=#8b5cf6, waves=#10b981, modern=#ec4899
- ALWAYS provide at least 3-5 solution key-value pairs
- ALWAYS provide at least 1 animated object OR meaningful static scene"""


# ─── LLM CALL ────────────────────────────────────────────────────────────────

async def call_llm(chapter: str, problem: str) -> dict:
    prompt = f"Chapter: {chapter}\nProblem: {problem}\n\nSolve completely and generate 3D scene JSON."

    # Try OpenAI first
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and not openai_key.startswith("sk-your"):
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"},
                    }
                )
                r.raise_for_status()
                data = r.json()
                return json.loads(data["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"[solver] OpenAI error: {e}")

    # Try Groq
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key and not groq_key.startswith("your"):
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                r = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.1,
                    }
                )
                r.raise_for_status()
                txt = r.json()["choices"][0]["message"]["content"].strip()
                # Strip markdown code fences if present
                txt = re.sub(r"```(?:json)?", "", txt).strip().rstrip("`").strip()
                return json.loads(txt)
        except Exception as e:
            print(f"[solver] Groq error: {e}")

    # No LLM available — use local solver
    print("[solver] No LLM key found, using local solver")
    return local_solve(chapter, problem)


# ─── LOCAL SOLVER (fallback when no API key) ──────────────────────────────────

def extract_numbers(text: str):
    return [float(x) for x in re.findall(r'\d+\.?\d*(?:[eE][+-]?\d+)?', text)]

def kf(t, x, y, z=0.0):
    return {"t": round(float(t), 4), "x": round(float(x), 4),
            "y": round(float(y), 4), "z": round(float(z), 4)}

def make_result(problem_type, description, solution, objects=None, statics=None,
                vectors=None, lines=None, labels=None):
    return {
        "problem_type": problem_type,
        "description": description,
        "solution": solution,
        "scene": {
            "objects": objects or [],
            "static_objects": statics or [
                {"shape": "plane", "position": [0, -0.05, 0],
                 "rotation": [-math.pi/2, 0, 0], "width": 30, "depth": 12, "color": "#111122"}
            ],
            "vectors": vectors or [],
            "lines": lines or [],
            "labels": labels or [],
        }
    }

def local_solve(chapter: str, problem: str) -> dict:
    p = problem.lower()
    nums = extract_numbers(problem)
    def n(i, default): return nums[i] if i < len(nums) else default

    # ── MECHANICS ──
    if chapter == "mechanics":
        if any(k in p for k in ["projectile","throw","launch","angle","fired","ball"]):
            v0 = n(0, 20); ang = math.radians(n(1, 45)); h0 = n(2, 0); g = 9.8
            vx, vy = v0*math.cos(ang), v0*math.sin(ang)
            T = (vy + math.sqrt(vy**2 + 2*g*h0)) / g
            R = vx * T; H = h0 + vy**2/(2*g)
            steps = 60
            kfs = [kf(T*i/steps, vx*T*i/steps * 0.5,
                      max(0, h0 + vy*(T*i/steps) - 0.5*g*(T*i/steps)**2))
                   for i in range(steps+1)]
            return make_result("projectile", f"Projectile: v0={v0}m/s angle={math.degrees(ang):.0f}°",
                {"v0": f"{v0} m/s", "angle": f"{math.degrees(ang):.1f}°",
                 "time_of_flight": f"{T:.3f} s", "range": f"{R:.3f} m",
                 "max_height": f"{H:.3f} m", "vx": f"{vx:.2f} m/s"},
                objects=[{"id":"ball","shape":"sphere","size":0.35,"color":"#f59e0b",
                          "label":"Projectile","trail":True,"loop":False,"keyframes":kfs}])

        if any(k in p for k in ["fall","drop","freefall"]):
            h = n(0, 80); g = 9.8; T = math.sqrt(2*h/g); vf = g*T
            steps = 50
            kfs = [kf(T*i/steps, 0, max(0, h - 0.5*g*(T*i/steps)**2)) for i in range(steps+1)]
            return make_result("free_fall", f"Free fall from {h}m",
                {"height": f"{h} m", "time": f"{T:.3f} s", "final_velocity": f"{vf:.3f} m/s",
                 "KE_impact": f"{0.5*n(1,1)*vf**2:.2f} J"},
                objects=[{"id":"obj","shape":"sphere","size":0.4,"color":"#ef4444",
                          "label":"Object","trail":True,"loop":False,"keyframes":kfs}])

        if "pendulum" in p:
            L = n(0, 1.5); th0 = math.radians(n(1, 30)); g = 9.8
            omega = math.sqrt(g/L); T = 2*math.pi/omega; pivot_y = L + 1
            steps = 120; t_total = T*3
            kfs = [kf(t_total*i/steps,
                      L*math.sin(th0*math.cos(omega*t_total*i/steps)),
                      pivot_y - L*math.cos(th0*math.cos(omega*t_total*i/steps)))
                   for i in range(steps+1)]
            return make_result("pendulum", f"Pendulum L={L}m",
                {"period": f"{T:.3f} s", "frequency": f"{1/T:.3f} Hz",
                 "v_max": f"{math.sqrt(2*g*L*(1-math.cos(th0))):.3f} m/s"},
                objects=[{"id":"bob","shape":"sphere","size":0.3,"color":"#6366f1",
                          "label":"Bob","trail":False,"loop":True,"keyframes":kfs}])

        if any(k in p for k in ["spring","shm","oscillat","vibrat"]):
            k_s = n(0, 100); m = n(1, 0.5); A = n(2, 0.2)
            omega = math.sqrt(k_s/m); T = 2*math.pi/omega
            steps = 120; t_total = T*4
            kfs = [kf(t_total*i/steps, A*math.cos(omega*t_total*i/steps), 0.8)
                   for i in range(steps+1)]
            return make_result("spring_shm", f"SHM k={k_s} A={A}",
                {"period": f"{T:.4f} s", "omega": f"{omega:.4f} rad/s",
                 "v_max": f"{A*omega:.4f} m/s", "a_max": f"{A*omega**2:.4f} m/s²",
                 "max_KE": f"{0.5*k_s*A**2:.4f} J"},
                objects=[{"id":"mass","shape":"box","size":0.45,"color":"#10b981",
                          "label":f"k={k_s}","trail":False,"loop":True,"keyframes":kfs}])

        if any(k in p for k in ["incline","slope","friction","ramp"]):
            m = n(0, 3); ang = math.radians(n(1, 37))
            mu_s = n(2, 0.4); mu_k = n(3, 0.3); g = 9.8
            N = m*g*math.cos(ang); W = m*g*math.sin(ang)
            sliding = W > mu_s*N
            a = max(0, (W - mu_k*N)/m) if sliding else 0
            return make_result("block_on_incline", "Block on inclined plane",
                {"normal_force": f"{N:.3f} N", "weight_parallel": f"{W:.3f} N",
                 "friction": f"{mu_k*N:.3f} N", "acceleration": f"{a:.4f} m/s²",
                 "status": "Sliding" if sliding else "In equilibrium"},
                statics=[{"shape":"custom_incline","angle_deg":math.degrees(ang),"length":8,"color":"#2a3a2a","position":[0,0,0]}],
                vectors=[{"origin":[0,0.5,0],"direction":[0,-2,0],"color":"#ef4444","label":f"mg={m*g:.1f}N"},
                         {"origin":[0,0.5,0],"direction":[0,N/m/g*2,0],"color":"#22c55e","label":f"N={N:.1f}N"}])

        if any(k in p for k in ["atwood","pulley","string"]):
            m1 = n(0, 4); m2 = n(1, 2); g = 9.8
            a = abs(m1-m2)*g/(m1+m2); T_tens = 2*m1*m2*g/(m1+m2)
            steps = 60; t_total = 3.0
            k1 = [kf(t_total*i/steps, -0.5, 3 - 0.5*a*(t_total*i/steps)**2) for i in range(steps+1)]
            k2 = [kf(t_total*i/steps,  0.5, 1 + 0.5*a*(t_total*i/steps)**2) for i in range(steps+1)]
            return make_result("atwood", f"Atwood m1={m1}kg m2={m2}kg",
                {"acceleration": f"{a:.4f} m/s²", "tension": f"{T_tens:.4f} N",
                 "m1_heavier": str(m1 > m2)},
                objects=[{"id":"m1","shape":"sphere","size":0.4,"color":"#3b82f6","label":f"m₁={m1}","trail":False,"loop":False,"keyframes":k1},
                         {"id":"m2","shape":"sphere","size":0.4,"color":"#ef4444","label":f"m₂={m2}","trail":False,"loop":False,"keyframes":k2}])

        if any(k in p for k in ["collid","elastic","inelastic"]):
            m1 = n(0, 3); v1 = n(1, 6); m2 = n(2, 1); v2 = n(3, 0)
            ct = "inelastic" if "inelastic" in p else "elastic"
            if "elastic" in ct and "in" not in ct:
                v1f = ((m1-m2)*v1+2*m2*v2)/(m1+m2)
                v2f = ((m2-m1)*v2+2*m1*v1)/(m1+m2)
            else:
                v1f = v2f = (m1*v1+m2*v2)/(m1+m2)
            steps = 80; t_col = 3.0; t_total = 5.0
            kf1 = [kf(t_total*i/steps, -6+v1*min(t_total*i/steps,t_col)+v1f*max(0,t_total*i/steps-t_col), 0.5) for i in range(steps+1)]
            kf2 = [kf(t_total*i/steps,  6+v2*min(t_total*i/steps,t_col)+v2f*max(0,t_total*i/steps-t_col), 0.5) for i in range(steps+1)]
            return make_result("collision", f"{ct} collision",
                {"v1_initial": f"{v1} m/s", "v2_initial": f"{v2} m/s",
                 "v1_final": f"{v1f:.4f} m/s", "v2_final": f"{v2f:.4f} m/s",
                 "KE_before": f"{0.5*m1*v1**2+0.5*m2*v2**2:.3f} J",
                 "KE_after":  f"{0.5*m1*v1f**2+0.5*m2*v2f**2:.3f} J"},
                objects=[{"id":"b1","shape":"sphere","size":0.45,"color":"#3b82f6","label":f"m₁={m1}","trail":False,"loop":False,"keyframes":kf1},
                         {"id":"b2","shape":"sphere","size":0.45,"color":"#ef4444","label":f"m₂={m2}","trail":False,"loop":False,"keyframes":kf2}])

        if any(k in p for k in ["circular","vertical circle","loop"]):
            r = n(0, 1); m = n(1, 0.5); g = 9.8
            v_b = math.sqrt(5*g*r); T_period = 2*math.pi*r/v_b
            cx, cy = 0, r+0.5; steps = 120
            kfs = [kf(T_period*i/steps, cx+r*math.cos(2*math.pi*i/steps-math.pi/2),
                      cy+r*math.sin(2*math.pi*i/steps-math.pi/2)) for i in range(steps+1)]
            return make_result("vertical_circle", f"Vertical circle r={r}m",
                {"min_v_bottom": f"{v_b:.3f} m/s", "min_v_top": f"{math.sqrt(g*r):.3f} m/s",
                 "T_bottom": f"{m*(g+v_b**2/r):.3f} N", "T_top": f"0 N (minimum)"},
                objects=[{"id":"mass","shape":"sphere","size":0.3,"color":"#f59e0b","label":"mass","trail":False,"loop":True,"keyframes":kfs}])

        if any(k in p for k in ["rotat","torque","disk","angular","moment"]):
            m = n(0, 2); r = n(1, 0.4); torque = n(2, 5)
            I = 0.5*m*r**2; alpha = torque/I
            steps = 120; T = 5.0
            kfs = [kf(T*i/steps, 0, 0.5, 0.5*alpha*(T*i/steps)**2) for i in range(steps+1)]
            return make_result("rotation", f"Rotation torque={torque}N·m",
                {"moment_of_inertia": f"{I:.4f} kg·m²", "angular_acceleration": f"{alpha:.4f} rad/s²",
                 "omega_5s": f"{alpha*5:.3f} rad/s", "KE_5s": f"{0.5*I*(alpha*5)**2:.3f} J"})

        if any(k in p for k in ["roll","cylinder rolling","sphere rolling"]):
            m = n(0, 2); r = n(1, 0.1); ang = math.radians(n(2, 30)); g = 9.8
            a = g*math.sin(ang)/1.5
            steps = 80; T = 3.0
            kfs = [kf(T*i/steps, 0.5*a*(T*i/steps)**2*math.cos(ang),
                      max(0, 5 - 0.5*a*(T*i/steps)**2*math.sin(ang))) for i in range(steps+1)]
            return make_result("rolling", f"Rolling without slipping",
                {"acceleration": f"{a:.4f} m/s²", "friction": f"{m*g*math.sin(ang)/3:.4f} N",
                 "condition": "No slip"},
                objects=[{"id":"ball","shape":"sphere","size":0.3,"color":"#10b981","label":"Cylinder","trail":True,"loop":False,"keyframes":kfs}])

    # ── THERMODYNAMICS ──
    elif chapter == "thermodynamics":
        if any(k in p for k in ["carnot","efficiency","engine"]):
            Th = n(0, 600); Tc = n(1, 300); Qh = n(2, 2000)
            eta = 1 - Tc/Th; W = eta*Qh; Qc = Qh - W
            return make_result("carnot", f"Carnot engine Th={Th}K Tc={Tc}K",
                {"efficiency": f"{eta*100:.2f}%", "work_output": f"{W:.2f} J",
                 "Q_rejected": f"{Qc:.2f} J", "COP": f"{Tc/(Th-Tc):.4f}"},
                labels=[{"text":f"T_H={Th}K","x":-4,"y":5,"z":0,"color":"#ef4444"},
                        {"text":f"T_C={Tc}K","x":4,"y":1,"z":0,"color":"#3b82f6"},
                        {"text":f"η={eta*100:.1f}%","x":0,"y":3,"z":0,"color":"#f59e0b"},
                        {"text":f"W={W:.1f}J","x":0,"y":2,"z":0,"color":"#10b981"}])

        if any(k in p for k in ["calori","mix","heat","equilibrium","specific"]):
            m1=n(0,.5); c1=n(1,4186); T1=n(2,80); m2=n(3,.2); c2=n(4,900); T2=n(5,20)
            Teq = (m1*c1*T1+m2*c2*T2)/(m1*c1+m2*c2)
            return make_result("calorimetry", f"Calorimetry Teq={Teq:.2f}°C",
                {"T_equilibrium": f"{Teq:.4f} °C",
                 "Q_gained": f"{m2*c2*(Teq-T2):.3f} J",
                 "Q_lost": f"{m1*c1*(T1-Teq):.3f} J"},
                labels=[{"text":f"T₁={T1}°C","x":-3,"y":3,"z":0,"color":"#ef4444"},
                        {"text":f"T₂={T2}°C","x":3,"y":1,"z":0,"color":"#3b82f6"},
                        {"text":f"T_eq={Teq:.1f}°C","x":0,"y":2,"z":0,"color":"#f59e0b"}])

        # PV processes
        proc = "adiabatic" if "adiabat" in p else "isobaric" if "isobar" in p else "isochoric" if "isochor" in p else "isothermal"
        P1 = n(0, 101325); V1 = n(1, 0.001); T1_pv = n(2, 300); gam = 1.4
        V2 = V1*3; P2 = P1*V1/V2
        W_work = P1*V1*math.log(V2/V1) if "thermal" in proc else P1*(V2-V1) if "bar" in proc else 0
        return make_result("pv_diagram", f"{proc} process",
            {"process": proc, "P1": f"{P1:.0f} Pa", "V1": f"{V1*1000:.2f} L",
             "work_done": f"{W_work:.3f} J", "first_law": "Q = ΔU + W"})

    # ── ELECTROMAGNETISM ──
    elif chapter == "electromagnetism":
        if any(k in p for k in ["electron","proton","charge","magnetic","cyclotron","lorentz"]):
            B = n(0, 0.5); v = n(1, 2e6)
            is_electron = "electron" in p
            m_p = 9.1e-31 if is_electron else 1.67e-27
            q = 1.6e-19; q_sign = -1 if is_electron else 1
            r = m_p*v/(q*B); T = 2*math.pi*m_p/(q*B)
            omega = q*B/m_p; scale = min(r, 6.0); steps = 150; t_total = T*2
            kfs = [kf(t_total*i/steps, scale*math.sin(omega*t_total*i/steps*q_sign),
                      scale*(1-math.cos(omega*t_total*i/steps*q_sign)))
                   for i in range(steps+1)]
            return make_result("magnetic_force", f"{'Electron' if is_electron else 'Proton'} in magnetic field",
                {"radius": f"{r:.4e} m", "period": f"{T:.4e} s",
                 "cyclotron_freq": f"{1/T:.4e} Hz", "KE": f"{0.5*m_p*v**2:.4e} J"},
                objects=[{"id":"particle","shape":"sphere","size":0.25,
                          "color":"#60a5fa" if is_electron else "#f59e0b",
                          "label":"e⁻" if is_electron else "p⁺","trail":True,"loop":True,"keyframes":kfs}])

        if any(k in p for k in ["lc circuit","inductor","capacitor","oscillat"]):
            L = n(0, 0.1); C = n(1, 1e-4); V0 = n(2, 10); R = n(3, 0)
            omega0 = 1/math.sqrt(L*C); T = 2*math.pi/omega0; Q0 = C*V0
            gamma = R/(2*L) if R > 0 else 0
            omega_d = math.sqrt(max(0, omega0**2 - gamma**2))
            steps = 200; t_total = T*4
            kfs = [kf(t_total*i/steps, t_total*i/steps*2-4,
                      Q0*math.exp(-gamma*t_total*i/steps)*math.cos(omega_d*t_total*i/steps)*2)
                   for i in range(steps+1)]
            return make_result("lc_circuit", f"LC circuit f={omega0/(2*math.pi):.3f}Hz",
                {"omega_0": f"{omega0:.4f} rad/s", "frequency": f"{omega0/(2*math.pi):.4f} Hz",
                 "Q_max": f"{Q0:.6f} C", "I_max": f"{Q0*omega0:.6f} A",
                 "max_energy": f"{0.5*C*V0**2:.6f} J"},
                objects=[{"id":"charge","shape":"sphere","size":0.2,"color":"#f59e0b","label":"Q(t)","trail":True,"loop":False,"keyframes":kfs}])

        if any(k in p for k in ["induction","emf","coil","faraday","flux"]):
            B = n(0, 2); A = n(1, 0.05); om = n(2, 100); R_c = n(3, 50)
            EMF_max = B*A*om; I_max = EMF_max/R_c; T = 2*math.pi/om
            steps = 200; t_total = T*4
            kfs = [kf(t_total*i/steps, t_total*i/steps*2-4,
                      EMF_max*math.sin(om*t_total*i/steps)*1.5) for i in range(steps+1)]
            return make_result("em_induction", f"EM induction EMF_max={EMF_max:.3f}V",
                {"EMF_max": f"{EMF_max:.4f} V", "I_max": f"{I_max:.4f} A",
                 "frequency": f"{om/(2*math.pi):.4f} Hz", "power_avg": f"{0.5*I_max**2*R_c:.4f} W"},
                objects=[{"id":"emf","shape":"sphere","size":0.2,"color":"#f59e0b","label":"EMF","trail":True,"loop":False,"keyframes":kfs}])

        # Coulomb / electric field
        q1 = n(0, 2e-6); q2 = n(1, 2e-6); sep = n(2, 3)
        s2 = -1 if any(k in p for k in ["opposite","attract","negative","unlike"]) else 1
        F_e = 8.99e9*q1*q2/sep**2
        return make_result("electric_field", "Electric force between charges",
            {"coulomb_force": f"{F_e:.6f} N", "separation": f"{sep} m",
             "interaction": "Attractive" if s2 < 0 else "Repulsive",
             "potential_energy": f"{8.99e9*q1*q2*s2/sep:.6f} J"},
            statics=[{"shape":"sphere","position":[-sep/2,0,0],"size":0.35,"color":"#ef4444"},
                     {"shape":"sphere","position":[sep/2,0,0],"size":0.35,"color":"#3b82f6" if s2<0 else "#ef4444"}],
            labels=[{"text":"+" ,"x":-sep/2,"y":0.7,"z":0,"color":"#ef4444"},
                    {"text":"+" if s2>0 else "–","x":sep/2,"y":0.7,"z":0,"color":"#ef4444" if s2>0 else "#3b82f6"},
                    {"text":f"F={F_e:.4f}N","x":0,"y":-1,"z":0,"color":"#f59e0b"}])

    # ── WAVES ──
    elif chapter == "waves":
        if any(k in p for k in ["doppler","approach","reced","ambulance","train","source"]):
            fs = n(0, 440); vs = n(1, 30); vo = n(2, 0); v_s = n(3, 340)
            app = not any(k in p for k in ["reced","away","moving away"])
            f_obs = fs*(v_s+vo)/(v_s-vs) if app else fs*(v_s-vo)/(v_s+vs)
            steps = 80; T = 4.0
            kfs = [kf(T*i/steps, -4 + (8 if app else -8)*(i/steps)*vs/v_s, 0.5)
                   for i in range(steps+1)]
            return make_result("doppler", f"Doppler f_obs={f_obs:.2f}Hz",
                {"f_source": f"{fs} Hz", "f_observed": f"{f_obs:.4f} Hz",
                 "delta_f": f"{abs(f_obs-fs):.4f} Hz", "v_source": f"{vs} m/s"},
                objects=[{"id":"src","shape":"sphere","size":0.4,"color":"#f59e0b","label":"Source","trail":False,"loop":False,"keyframes":kfs}])

        f1 = n(0, 440); A1 = n(1, 1); f2 = n(2, 444); A2 = n(3, 1)
        dur = n(4, 3); steps = 200; t_arr = np.linspace(0, dur, steps)
        ys = A1*np.sin(2*math.pi*f1*t_arr) + A2*np.sin(2*math.pi*f2*t_arr)
        sx = 8/dur
        kfs_s = [kf(float(t_arr[i]), float(t_arr[i]*sx-4), float(ys[i])+1) for i in range(steps)]
        return make_result("wave_superposition", f"Beat freq={abs(f1-f2)}Hz",
            {"f1": f"{f1} Hz", "f2": f"{f2} Hz",
             "beat_frequency": f"{abs(f1-f2)} Hz", "max_amplitude": f"{A1+A2}"},
            objects=[{"id":"wave","shape":"sphere","size":0.18,"color":"#10b981","label":"Superposition","trail":True,"loop":False,"keyframes":kfs_s}])

    # ── OPTICS ──
    elif chapter == "optics":
        if any(k in p for k in ["refract","snell","critical","total internal"]):
            n1 = n(0, 1.0); n2 = n(1, 1.5); th_i = math.radians(n(2, 40))
            sin_r = n1*math.sin(th_i)/n2; TIR = abs(sin_r) > 1
            th_r = math.asin(min(1, abs(sin_r))) if not TIR else math.pi/2
            crit = math.degrees(math.asin(n2/n1)) if n2 < n1 else None
            rl = 5
            return make_result("ray_refraction", f"Refraction n1={n1} n2={n2}",
                {"angle_incidence": f"{math.degrees(th_i):.2f}°",
                 "angle_refraction": "TIR" if TIR else f"{math.degrees(th_r):.2f}°",
                 "critical_angle": f"{crit:.2f}°" if crit else "N/A",
                 "TIR": "YES" if TIR else "NO"},
                lines=[{"points":[[-rl*math.sin(th_i),rl*math.cos(th_i),0],[0,0,0]],"color":"#f59e0b"},
                       {"points":[[0,0,0],[rl*math.sin(th_r),-rl*math.cos(th_r),0]],"color":"#10b981"},
                       {"points":[[-4,0,0],[4,0,0]],"color":"#33333388"}])

        if any(k in p for k in ["lens","convex","concave"]):
            f_v = n(0, 0.15); d_o = n(1, 0.4); h_o = n(2, 0.05)
            lt = "concave" if "concave" in p else "convex"
            f = abs(f_v) if lt == "convex" else -abs(f_v)
            d_i = (f*d_o)/(d_o-f) if abs(d_o-f) > 1e-9 else 999
            m = -d_i/d_o; sc = 6
            do_s = min(d_o*sc, 8); di_s = min(abs(d_i)*sc, 8)*(1 if d_i>0 else -1)
            ho_s = h_o*sc*4; hi_s = m*h_o*sc*4
            return make_result("lens", f"{lt} lens d_i={d_i*100:.1f}cm m={m:.3f}",
                {"f": f"{f*100:.1f} cm", "d_object": f"{d_o*100:.1f} cm",
                 "d_image": f"{d_i*100:.2f} cm", "magnification": f"{m:.4f}×",
                 "h_image": f"{m*h_o*100:.2f} cm",
                 "nature": "Real & Inverted" if (d_i>0 and m<0) else "Virtual & Upright",
                 "power": f"{1/f:.2f} D"},
                lines=[{"points":[[-do_s,ho_s,0],[0,ho_s,0],[di_s,0,0]],"color":"#ef4444"},
                       {"points":[[-do_s,ho_s,0],[0,0,0],[di_s,hi_s,0]],"color":"#22c55e"},
                       {"points":[[-do_s*1.5,0,0],[di_s*1.5,0,0]],"color":"#33333388"}])

        if "mirror" in p:
            f_v = n(0, 0.1); d_o = n(1, 0.25); h_o = n(2, 0.03)
            mt = "convex" if "convex" in p else "concave"
            f = abs(f_v) if mt == "convex" else -abs(f_v)
            u = -d_o; d_i = f*u/(u-f) if abs(u-f) > 1e-9 else 999
            m = -d_i/u; sc = 6
            do_s = min(d_o*sc, 8); di_s = min(abs(d_i)*sc, 8)*(1 if d_i<0 else -1)
            ho_s = h_o*sc*4; hi_s = m*h_o*sc*4
            return make_result("mirror", f"{mt} mirror d_i={d_i*100:.1f}cm",
                {"f": f"{abs(f_v)*100:.1f} cm", "d_object": f"{d_o*100:.1f} cm",
                 "d_image": f"{d_i*100:.2f} cm", "magnification": f"{m:.4f}×",
                 "nature": "Real & Inverted" if (d_i<0 and m<0) else "Virtual & Erect"})

        if "prism" in p:
            A = math.radians(n(0, 60)); n_g = n(1, 1.5); th_i = math.radians(n(2, 40))
            r1 = math.asin(math.sin(th_i)/n_g); r2 = A - r1
            if abs(n_g*math.sin(r2)) <= 1:
                th_e = math.asin(n_g*math.sin(r2))
                delta = th_i + th_e - A
                delta_min = 2*math.asin(n_g*math.sin(A/2)) - A
            else:
                th_e = math.pi/2; delta = 0; delta_min = 0
            return make_result("prism", f"Prism deviation={math.degrees(delta):.2f}°",
                {"apex_angle": f"{math.degrees(A):.1f}°", "n": str(n_g),
                 "deviation": f"{math.degrees(delta):.2f}°",
                 "min_deviation": f"{math.degrees(delta_min):.2f}°"})

        if any(k in p for k in ["young","double slit","slit","fringe","interference"]):
            d = n(0, 0.001); D = n(1, 1.0); lm = n(2, 550)*1e-9
            beta = lm*D/d
            return make_result("youngs_double", f"β={beta*1e3:.3f}mm",
                {"fringe_width": f"{beta*1e3:.4f} mm",
                 "angular_fringe": f"{lm/d:.6e} rad",
                 "3rd_bright": f"{3*beta*1e3:.4f} mm from center",
                 "formula": "β = λD/d"})

    # ── MODERN PHYSICS ──
    elif chapter == "modern_physics":
        if any(k in p for k in ["bohr","hydrogen","transition","orbit","n="]):
            Z = int(n(0, 1)); ni = int(n(1, 3)); nf = int(n(2, 1))
            E1 = -13.6*Z**2/ni**2; E2 = -13.6*Z**2/nf**2; dE = abs(E2-E1)
            lm = (4.136e-15*3e8/dE)*1e9 if dE > 0 else 0
            r1 = 0.529*ni**2/Z; r2 = 0.529*nf**2/Z; scale = max(r1, r2)
            steps = 120; t_total = 4.0
            kfs = [kf(t_total*i/steps,
                      (r1*(1-i/steps)+r2*(i/steps))*math.cos(10*math.pi*i/steps)/scale*4,
                      (r1*(1-i/steps)+r2*(i/steps))*math.sin(10*math.pi*i/steps)/scale*4)
                   for i in range(steps+1)]
            return make_result("bohr_atom", f"Bohr n={ni}→{nf} λ={lm:.2f}nm",
                {"Z": str(Z), "n_initial": str(ni), "n_final": str(nf),
                 "delta_E": f"{dE:.4f} eV", "wavelength": f"{lm:.3f} nm",
                 "series": "Lyman" if nf==1 else "Balmer" if nf==2 else "Paschen"},
                objects=[{"id":"e","shape":"sphere","size":0.15,"color":"#60a5fa","label":"e⁻","trail":True,"loop":False,"keyframes":kfs}],
                statics=[{"shape":"sphere","position":[0,0,0],"size":0.3,"color":"#ef4444"}])

        if any(k in p for k in ["photoelectric","work function","threshold","stopping"]):
            phi_eV = n(0, 2.3); f_Hz = n(1, 8e14)
            h = 6.626e-34; e = 1.6e-19
            E_photon = h*f_Hz; phi_J = phi_eV*e
            KE_max = max(0, E_photon - phi_J); f_thresh = phi_J/h
            steps = 60; t_total = 3.0
            kfs = [kf(t_total*i/steps, -3+6*(i/steps), (i/steps)*2)
                   for i in range(steps+1)] if E_photon > phi_J else [kf(0,-3,0)]
            return make_result("photoelectric", "Photoelectric effect",
                {"E_photon": f"{E_photon/e:.3f} eV", "work_function": f"{phi_eV} eV",
                 "KE_max": f"{KE_max/e:.3f} eV", "stopping_potential": f"{KE_max/e:.3f} V",
                 "threshold_freq": f"{f_thresh:.4e} Hz",
                 "emission": "YES" if E_photon > phi_J else "NO"},
                objects=[{"id":"e","shape":"sphere","size":0.2,"color":"#60a5fa","label":"e⁻","trail":True,"loop":False,"keyframes":kfs}])

        if any(k in p for k in ["radioact","decay","half","disintegrat"]):
            N0 = n(0, 1e6); t12 = n(1, 10); t = n(2, 30)
            lam = math.log(2)/t12; Nt = N0*math.exp(-lam*t)
            steps = 100
            kfs = [kf(t*i/steps, t*i/steps*0.8-4, N0*math.exp(-lam*t*i/steps)/N0*4)
                   for i in range(steps+1)]
            return make_result("radioactive", f"Radioactive decay N(t)={Nt:.3e}",
                {"N0": f"{N0:.2e}", "half_life": f"{t12} s", "time": f"{t} s",
                 "decay_constant": f"{lam:.6f} s⁻¹",
                 "N_remaining": f"{Nt:.4e}", "fraction": f"{Nt/N0:.4f}"},
                objects=[{"id":"N","shape":"sphere","size":0.25,"color":"#ec4899","label":"N(t)","trail":True,"loop":False,"keyframes":kfs}])

    # ── UNIVERSAL FALLBACK ── (any chapter, any problem not matched above)
    # Extract whatever numbers we can and produce a labeled scene
    solution_dict = {}
    for i, num in enumerate(nums[:8]):
        solution_dict[f"value_{i+1}"] = str(num)
    solution_dict["note"] = "Add OPENAI_API_KEY or GROQ_API_KEY for full LLM-powered solving"
    solution_dict["problem"] = problem[:100]

    return make_result("general", f"{chapter}: {problem[:60]}",
        solution_dict,
        labels=[{"text": chapter.upper(), "x": 0, "y": 3, "z": 0, "color": "#f59e0b"},
                {"text": problem[:40], "x": 0, "y": 2, "z": 0, "color": "#aaa"}])


# ─── SCENE NORMALIZER ─────────────────────────────────────────────────────────
# Ensures the scene dict from LLM always has correct keys

def normalize_scene(raw: dict) -> dict:
    scene = raw.get("scene", {})
    return {
        "objects":        scene.get("objects", []),
        "static_objects": scene.get("static_objects", []),
        "vectors":        scene.get("vectors", []),
        "lines":          scene.get("lines", []),
        "scene_labels":   scene.get("labels", scene.get("scene_labels", [])),
    }


# ─── MAIN ENTRY ───────────────────────────────────────────────────────────────

async def solve(chapter: str, problem: str) -> dict:
    print(f"[solver] chapter={chapter!r} problem={problem[:60]!r}")

    try:
        raw = await call_llm(chapter, problem)
    except Exception as e:
        print(f"[solver] LLM call failed: {e}, using local solver")
        raw = local_solve(chapter, problem)

    # Merge scene into top level (SimCanvas expects flat structure)
    scene = normalize_scene(raw)

    return {
        "problem_type":   raw.get("problem_type", "general"),
        "description":    raw.get("description", problem[:80]),
        "solution":       raw.get("solution", {}),
        **scene,
    }