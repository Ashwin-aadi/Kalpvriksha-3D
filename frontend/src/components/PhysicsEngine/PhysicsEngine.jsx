import { useState, useRef } from 'react';
import { SimCanvas } from './SimCanvas.jsx';
import { ProblemPanel } from './ProblemPanel.jsx';

// ── Step-by-step solution builder ─────────────────────────────────────────────
// Reads actual solution values and constructs pedagogically correct explanations
function buildSteps(simData) {
  if (!simData?.solution) return [];
  const sol = simData.solution;
  const type = (simData.problem_type || '').toLowerCase();
  const has = (...keys) => keys.some(k => Object.keys(sol).some(s => s.toLowerCase().includes(k)));
  const get = (...keys) => {
    for (const k of keys) {
      const found = Object.entries(sol).find(([s]) => s.toLowerCase().includes(k));
      if (found) return { key: found[0], val: found[1] };
    }
    return null;
  };
  const fmt = (...keys) => {
    const r = get(...keys);
    return r ? String(r.val) : '—';
  };

  // ── MECHANICS ──────────────────────────────────────────────────────────────
  if (type.includes('projectile')) return [
    { icon:'📐', head:'Resolve initial velocity',
      body:`Split v₀ into components using the launch angle θ:\n  vₓ = v₀·cos θ = ${fmt('vx')}\n  vᵧ₀ = v₀·sin θ = ${fmt('vy')}\nHorizontal vₓ stays constant throughout (no horizontal force).` },
    { icon:'⏱', head:'Time of flight',
      body:`At landing, vertical displacement = 0 (or −h for cliff).\nUsing  y = vᵧ₀t − ½gt²  →  solve for t:\n  t_flight = ${fmt('time','flight','total_time')}` },
    { icon:'📏', head:'Range (horizontal distance)',
      body:`R = vₓ × t_flight\n  R = ${fmt('range')}` },
    { icon:'⬆', head:'Maximum height',
      body:`At apex, vᵧ = 0.  Use  vᵧ² = vᵧ₀² − 2g·H:\n  H_max = vᵧ₀² / (2g) = ${fmt('height','max_height','hmax')}` },
    { icon:'💥', head:'Impact velocity',
      body:`At impact: vₓ unchanged, vᵧ = vᵧ₀ − g·t\n  v_impact = √(vₓ² + vᵧ²) = ${fmt('impact','v_impact','final_vel')}` },
  ];

  if (type.includes('free_fall')) return [
    { icon:'📐', head:'Setup', body:`Object released from rest (u=0) under gravity g = 9.8 m/s².\nHeight h = ${fmt('height','h')}` },
    { icon:'⏱', head:'Time to fall', body:`Using  s = ½gt²:\n  t = √(2h/g) = ${fmt('time','t_fall','t')}` },
    { icon:'🏃', head:'Final velocity', body:`v = g·t  (or  v = √(2gh))\n  v = ${fmt('velocity','v_final','final_vel','speed')}` },
    { icon:'⚡', head:'Kinetic energy at impact', body:`KE = ½mv² = mgh  (all PE converted)\n  KE = ${fmt('ke','kinetic','energy')}` },
  ];

  if (type.includes('pendulum')) return [
    { icon:'📐', head:'Setup', body:`Pendulum length L = ${fmt('length','l')}\nInitial angle θ = ${fmt('angle','theta')}\nSmall angle approx. valid for θ < 15°` },
    { icon:'🔄', head:'Period & frequency', body:`T = 2π√(L/g) = ${fmt('period','t_period')}\nf = 1/T = ${fmt('frequency','freq')}\nNote: period independent of mass and amplitude (for small angles)` },
    { icon:'💨', head:'Maximum velocity', body:`At lowest point all PE → KE:\n  v_max = √(2gL(1−cosθ)) = ${fmt('v_max','vmax','max_vel','max_velocity')}` },
    { icon:'⚡', head:'Total mechanical energy', body:`E = mgh_max = mgL(1−cosθ)\n  E = ${fmt('energy','total_energy','e_total')}` },
  ];

  if (type.includes('vertical_circle')||type.includes('vertical circle')) return [
    { icon:'📐', head:'Setup', body:`Mass m = ${fmt('mass','m')}  Radius R = ${fmt('radius','r')}` },
    { icon:'⚡', head:'Minimum speed at bottom', body:`For complete circle, at top: T_top ≥ 0\nAt top:  mg = mv²_top/R  →  v_top_min = √(gR)\nUsing energy:  v_bottom_min = √(5gR) = ${fmt('v_min','vmin','min_speed','v_bottom')}` },
    { icon:'🔗', head:'Tension at bottom', body:`T_bottom − mg = mv²/R\n  T_bottom = ${fmt('tension','t_bottom','tension_bottom')}` },
    { icon:'🔗', head:'Tension at top', body:`T_top + mg = mv²_top/R\n  T_top = ${fmt('t_top','tension_top')} (0 at minimum speed)` },
  ];

  if (type.includes('spring')||type.includes('shm')) return [
    { icon:'📐', head:'Setup', body:`Spring constant k = ${fmt('k','spring_k')}\nMass m = ${fmt('mass','m')}\nAmplitude A = ${fmt('amplitude','a')}` },
    { icon:'🔄', head:'Angular frequency & period', body:`ω = √(k/m) = ${fmt('omega','w','angular')}\nT = 2π/ω = 2π√(m/k) = ${fmt('period','t_period')}\nNote: period depends only on m and k, not amplitude.` },
    { icon:'💨', head:'Max velocity & acceleration', body:`v_max = Aω  (at equilibrium) = ${fmt('v_max','vmax','max_vel')}\na_max = Aω² (at extremes) = ${fmt('a_max','amax','max_acc')}` },
    { icon:'⚡', head:'Energy', body:`E = ½kA²  (constant throughout)\n  E = ${fmt('energy','ke','total_energy')}` },
  ];

  if (type.includes('block_on_incline')||type.includes('incline')) return [
    { icon:'📐', head:'Force analysis', body:`Weight component along slope: mg·sinθ = ${fmt('parallel','mg_sin','along')}\nNormal force N = mg·cosθ = ${fmt('normal','n')}` },
    { icon:'🔍', head:'Friction forces', body:`Max static friction = μₛ·N = ${fmt('static_friction','f_static','max_static')}\nKinetic friction = μₖ·N = ${fmt('kinetic_friction','f_kinetic')}\nCompare driving force with max static friction to check motion.` },
    { icon:'📊', head:'Motion decision', body:`Net force along slope = ${fmt('net_force','fnet')}\nResult: ${fmt('status','motion','result')}\nAcceleration a = ${fmt('acceleration','a')}` },
  ];

  if (type.includes('atwood')) return [
    { icon:'📐', head:'Setup', body:`m₁ = ${fmt('m1','mass1')}  m₂ = ${fmt('m2','mass2')}\nAssume m₁ > m₂ (heavier side descends)` },
    { icon:'⚙', head:'Apply Newton\'s 2nd law', body:`Net force = (m₁−m₂)g\nTotal inertia = m₁+m₂\n  a = (m₁−m₂)g / (m₁+m₂) = ${fmt('acceleration','a')}` },
    { icon:'🔗', head:'Tension in string', body:`For m₂:  T − m₂g = m₂a\n  T = 2m₁m₂g / (m₁+m₂) = ${fmt('tension','t')}` },
  ];

  if (type.includes('elastic_collision')||type.includes('collision')) return [
    { icon:'📐', head:'Before collision', body:`v₁ = ${fmt('v1_initial','u1','v1i')}  v₂ = ${fmt('v2_initial','u2','v2i','v2')||'0 (at rest)'}` },
    { icon:'⚖', head:'Conservation of momentum', body:`m₁v₁ + m₂v₂ = m₁v₁' + m₂v₂'\n(Total momentum conserved in all collisions)` },
    { icon:'⚡', head:'Conservation of KE (elastic only)', body:`½m₁v₁² + ½m₂v₂² = ½m₁v₁'² + ½m₂v₂'²\ne = 1 for elastic collision` },
    { icon:'🏃', head:'After collision velocities', body:`v₁' = ${fmt('v1_final','v1f')}\nv₂' = ${fmt('v2_final','v2f')}` },
    { icon:'📊', head:'Energy check', body:`KE_before = ${fmt('ke_before')}\nKE_after  = ${fmt('ke_after')}\nLost = ${fmt('ke_lost','energy_lost')||'0 (elastic)'}` },
  ];

  if (type.includes('rolling')) return [
    { icon:'📐', head:'Rolling without slipping', body:`Linear and rotational motion linked: v = Rω\nFor solid cylinder: I = ½MR²` },
    { icon:'⚙', head:'Acceleration on incline', body:`a = g·sinθ / (1 + I/MR²)\nFor solid cylinder: a = (2/3)g·sinθ = ${fmt('acceleration','a')}` },
    { icon:'⚡', head:'Kinetic energy', body:`KE_total = KE_trans + KE_rot = ½mv² + ½Iω²\n  = ${fmt('ke','energy','total_ke')}` },
  ];

  // ── THERMODYNAMICS ────────────────────────────────────────────────────────
  if (type.includes('calorimetry')) return [
    { icon:'🌡', head:'Principle of calorimetry', body:`Heat lost by hot body = Heat gained by cold body\n  Q_lost = Q_gained` },
    { icon:'⚙', head:'Set up equation', body:`m₁c₁(T₁−T_eq) = m₂c₂(T_eq−T₂)\nSolve for T_eq.` },
    { icon:'📊', head:'Equilibrium temperature', body:`T_eq = ${fmt('temp','equil','t_eq','temperature','equilibrium')}` },
    { icon:'💡', head:'Note', body:`If phase change occurs, latent heat L must be included: Q = mL` },
  ];

  if (type.includes('carnot')) return [
    { icon:'🌡', head:'Carnot efficiency (maximum possible)', body:`η = 1 − T_cold/T_hot\n  η = ${fmt('efficiency','eta','eff')}` },
    { icon:'⚙', head:'Work output', body:`W = η × Q_hot\n  W = ${fmt('work','w')}` },
    { icon:'❄', head:'Heat rejected to cold reservoir', body:`Q_cold = Q_hot − W\n  Q_cold = ${fmt('q_cold','rejected','heat_rejected')}` },
    { icon:'💡', head:'Key insight', body:`No real engine can exceed Carnot efficiency.\nCarnot engine is reversible and operates between two temperatures only.` },
  ];

  if (type.includes('isothermal')) return [
    { icon:'📐', head:'Isothermal process (T = const)', body:`T = ${fmt('temperature','t')}\nUsing ideal gas law: PV = nRT = constant` },
    { icon:'⚙', head:'Work done by gas', body:`W = nRT·ln(V₂/V₁) = P₁V₁·ln(V₂/V₁)\n  W = ${fmt('work','w')}` },
    { icon:'🔥', head:'First law check', body:`ΔU = 0 (temperature constant)\n  Q = W  (all heat converts to work)` },
  ];

  if (type.includes('adiabatic')) return [
    { icon:'📐', head:'Adiabatic process (Q = 0)', body:`No heat exchange with surroundings.\nPV^γ = constant  where γ = Cp/Cv = ${fmt('gamma')||'1.4 (diatomic)'}` },
    { icon:'🔄', head:'Final state', body:`P₂ = ${fmt('p2','p_final')}  V₂ = ${fmt('v2','v_final')}  T₂ = ${fmt('t2','t_final')}` },
    { icon:'⚙', head:'Work done', body:`W = (P₁V₁ − P₂V₂) / (γ−1)\n  W = ${fmt('work','w')}` },
    { icon:'🔥', head:'First law', body:`ΔU = −W  (internal energy decreases when gas expands adiabatically)` },
  ];

  if (type.includes('isobaric')) return [
    { icon:'📐', head:'Isobaric process (P = const)', body:`P = ${fmt('pressure','p')}` },
    { icon:'⚙', head:'Work done', body:`W = P·ΔV = P(V₂−V₁)\n  W = ${fmt('work','w')}` },
    { icon:'🔥', head:'Heat absorbed', body:`Q = nCp·ΔT = ${fmt('heat','q')}` },
    { icon:'💡', head:'Internal energy', body:`ΔU = Q − W = nCv·ΔT = ${fmt('delta_u','internal')}` },
  ];

  if (type.includes('heat_conduction')||type.includes('conduction')) return [
    { icon:'🌡', head:'Fourier\'s law', body:`Q/t = k·A·ΔT/L\nk = thermal conductivity, A = area, L = length` },
    { icon:'⚙', head:'Rate of heat transfer', body:`Q/t = ${fmt('rate','q_rate','heat_rate')}` },
  ];

  // ── ELECTROMAGNETISM ──────────────────────────────────────────────────────
  if (type.includes('electric')||type.includes('coulomb')) return [
    { icon:'⚡', head:'Coulomb\'s law', body:`F = k·q₁q₂/r²  where k = 9×10⁹ N·m²/C²\n  F = ${fmt('force','coulomb','f')}` },
    { icon:'↕', head:'Nature of force', body:`${fmt('interaction','nature','type_of_force')||'Attractive (opposite) / Repulsive (same)'}` },
    { icon:'💡', head:'Electric potential energy', body:`U = k·q₁q₂/r\n  U = ${fmt('potential_energy','u','pe','energy')}` },
    { icon:'🌐', head:'Electric field', body:`E = F/q = k·q/r²\n  E = ${fmt('field','e_field','electric_field')}` },
  ];

  if (type.includes('magnetic')||type.includes('cyclotron')) return [
    { icon:'🔄', head:'Lorentz force provides centripetal force', body:`qvB = mv²/r  →  r = mv/qB\n  r = ${fmt('radius','r')}` },
    { icon:'⏱', head:'Period & cyclotron frequency', body:`T = 2πm/qB  (independent of speed!)\n  T = ${fmt('period','t_period')}\n  f = ${fmt('frequency','freq')}` },
    { icon:'💡', head:'Key insight', body:`Cyclotron frequency is independent of particle speed.\nThis is the principle behind cyclotron accelerators.` },
  ];

  if (type.includes('lc_')||type.includes('lc circuit')||type.includes('damped')) return [
    { icon:'⚡', head:'LC oscillation frequency', body:`ω₀ = 1/√(LC) = ${fmt('omega','w','angular')}\nf = ω₀/2π = ${fmt('frequency','freq')}  T = ${fmt('period')}` },
    { icon:'🔋', head:'Charge and current', body:`Q_max = CV₀ = ${fmt('q_max','charge','max_charge')}\nI_max = Q_max·ω₀ = ${fmt('i_max','max_current','current')}` },
    { icon:'⚡', head:'Energy', body:`E = ½CV₀² = ½LI_max²\n  E = ${fmt('energy','e_total')}` },
    { icon:'📉', head:'Damping (if R present)', body:`Decay constant: α = R/2L = ${fmt('alpha','decay')}\nDamped frequency: ωd = √(ω₀²−α²) = ${fmt('omega_d','damped')}` },
  ];

  if (type.includes('em_')||type.includes('induction')||type.includes('emf')) return [
    { icon:'🔄', head:'Faraday\'s law', body:`EMF = −dΦ/dt = −N·d(BA)/dt` },
    { icon:'⚡', head:'Max EMF', body:`EMF_max = NBAω\n  EMF_max = ${fmt('emf','max_emf','e_max')}` },
    { icon:'💡', head:'Max current', body:`I_max = EMF_max / R = ${fmt('i_max','max_current','current')}` },
  ];

  // ── WAVES ─────────────────────────────────────────────────────────────────
  if (type.includes('doppler')) return [
    { icon:'🔊', head:'Doppler formula', body:`f_obs = f_source × (v ± v_obs) / (v ∓ v_source)\n+ for approaching, − for receding` },
    { icon:'📊', head:'Observed frequency', body:`f_observed = ${fmt('f_observed','f_obs','observed')}` },
    { icon:'💡', head:'Frequency shift', body:`Δf = f_observed − f_source = ${fmt('delta_f','shift','df')}\n${parseFloat(fmt('f_observed','f_obs'))||0 > parseFloat(fmt('f_source','f0'))||0 ? 'Source approaching → higher pitch' : 'Source receding → lower pitch'}` },
  ];

  if (type.includes('wave')||type.includes('beat')||type.includes('interference')||type.includes('resonance')) return [
    { icon:'🌊', head:'Superposition principle', body:`y_resultant = y₁ + y₂\n= A₁sin(ω₁t) + A₂sin(ω₂t)` },
    { icon:'🥁', head:'Beat frequency', body:`f_beat = |f₁ − f₂| = ${fmt('beat','f_beat','beat_freq')}\nBeats cause periodic loud/soft variation.` },
    { icon:'📊', head:'Amplitude range', body:`Constructive (max): A_max = A₁+A₂ = ${fmt('a_max','max_amplitude')}\nDestructive (min): A_min = |A₁−A₂| = ${fmt('a_min','min_amplitude')}` },
  ];

  // ── OPTICS ────────────────────────────────────────────────────────────────
  if (type.includes('refraction')||type.includes('snell')) return [
    { icon:'📐', head:'Snell\'s law', body:`n₁·sinθ₁ = n₂·sinθ₂\n  θ_refracted = ${fmt('angle_r','refracted','theta_r','theta2')}` },
    { icon:'🔍', head:'Critical angle & TIR', body:`θ_c = arcsin(n₂/n₁) = ${fmt('critical','critical_angle','theta_c')}\nTIR occurs when θ_incidence > θ_c:\n  TIR: ${fmt('tir','total_internal')||'check if incidence > critical angle'}` },
    { icon:'💡', head:'Optical path', body:`Denser medium → smaller angle (bends toward normal)\nRarer medium → larger angle (bends away from normal)` },
  ];

  if (type.includes('lens')) return [
    { icon:'📐', head:'Lens formula (New Cartesian)', body:`1/v − 1/u = 1/f\nSign convention: distances measured from optical centre` },
    { icon:'📏', head:'Image distance', body:`v = ${fmt('v','d_image','image_dist','image_distance')}` },
    { icon:'🔭', head:'Magnification', body:`m = v/u = ${fmt('magnification','m','mag')}\n|m| > 1 → magnified &nbsp; |m| < 1 → diminished\nm < 0 → inverted &nbsp; m > 0 → erect` },
    { icon:'🖼', head:'Nature of image', body:`${fmt('nature','image_nature','image_type','description')}` },
  ];

  if (type.includes('mirror')) return [
    { icon:'📐', head:'Mirror formula', body:`1/v + 1/u = 1/f = 2/R` },
    { icon:'📏', head:'Image distance', body:`v = ${fmt('v','d_image','image_dist')}` },
    { icon:'🔭', head:'Magnification & nature', body:`m = −v/u = ${fmt('magnification','m','mag')}\n${fmt('nature','image_nature','image_type')}` },
  ];

  if (type.includes('prism')) return [
    { icon:'📐', head:'Snell\'s law at first face', body:`n·sin(r₁) = sin(i)\n  r₁ = ${fmt('r1','angle_r1')}` },
    { icon:'⚙', head:'Geometry constraint', body:`r₁ + r₂ = A (prism apex angle)` },
    { icon:'📊', head:'Angle of deviation', body:`δ = (i + e) − A = ${fmt('deviation','delta','d')}\nMin deviation: δ_min = ${fmt('min_deviation','min_dev','d_min')}` },
  ];

  if (type.includes('young')||type.includes('slit')) return [
    { icon:'📐', head:'Young\'s double slit setup', body:`d = slit separation, D = screen distance, λ = wavelength` },
    { icon:'📏', head:'Fringe width', body:`β = λD/d = ${fmt('fringe','beta','fringe_width')}` },
    { icon:'📊', head:'Bright fringe positions', body:`y_n = nλD/d\n  3rd bright: y₃ = ${fmt('y3','3rd_bright','third_bright')}\n  2nd dark: y = ${fmt('2nd_dark','second_dark')}` },
  ];

  // ── MODERN PHYSICS ────────────────────────────────────────────────────────
  if (type.includes('photo')) return [
    { icon:'💡', head:'Photon energy', body:`E = hf  where h = 6.626×10⁻³⁴ J·s\n  E_photon = ${fmt('e_photon','photon_energy','e_ph')}` },
    { icon:'⚡', head:'Einstein photoelectric equation', body:`KE_max = hf − φ\n  KE_max = ${fmt('ke_max','ke','kinetic_max')}` },
    { icon:'🔌', head:'Stopping potential', body:`eV₀ = KE_max  →  V₀ = KE_max/e\n  V₀ = ${fmt('stopping','v_stop','v0')}` },
    { icon:'📊', head:'Threshold frequency', body:`φ = hf₀  →  f₀ = φ/h = ${fmt('threshold','f0','f_threshold')}\nEmission occurs only if f > f₀:\n  ${fmt('emission','result','status')||'Check if f > threshold'}` },
  ];

  if (type.includes('bohr')) return [
    { icon:'⚛', head:'Bohr energy levels', body:`Eₙ = −13.6×Z²/n²  eV\n  E_initial = ${fmt('e_initial','e1')}\n  E_final   = ${fmt('e_final','e2')}` },
    { icon:'📊', head:'Energy emitted', body:`ΔE = E_initial − E_final = ${fmt('delta_e','de','energy','energy_emitted')}\n(positive = photon emitted, negative = absorbed)` },
    { icon:'💡', head:'Wavelength of photon', body:`λ = hc/ΔE = ${fmt('wavelength','lambda')}\nSpectral series: ${fmt('series','spectral_series','line_series')}` },
  ];

  if (type.includes('radioact')) return [
    { icon:'☢', head:'Radioactive decay law', body:`N(t) = N₀·e^(−λt)\nλ = ln2/t½ = ${fmt('lambda','decay_const')}\nt½ = ${fmt('half_life','t_half')}` },
    { icon:'📊', head:'Atoms remaining', body:`N(t) = ${fmt('remaining','n_remaining','n_final','atoms')}\nFraction remaining = (½)^(t/t½) = ${fmt('fraction','frac')}` },
    { icon:'📉', head:'Activity', body:`A = λN  (decays per second)\n  A = ${fmt('activity','a_final','a_t')}` },
  ];

  // ── Generic fallback — show all solution keys nicely ──
  return Object.entries(sol).slice(0,8).map(([k,v])=>({
    icon:'📊', head: k.replace(/_/g,' '),
    body: String(v),
  }));
}

// ─────────────────────────────────────────────────────────────────────────────

const CH_COLOR = {
  mechanics:'#f59e0b', thermodynamics:'#ef4444',
  electromagnetism:'#3b82f6', waves:'#10b981',
  optics:'#8b5cf6', modern_physics:'#ec4899',
};
function accentFor(type) {
  const t=(type||'').toLowerCase();
  return Object.entries(CH_COLOR).find(([k])=>t.includes(k))?.[1]||'#f59e0b';
}

export function PhysicsEngine() {
  const [simData,   setSimData]   = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState('');
  const [playing,   setPlaying]   = useState(false);
  const canvasRef = useRef(null); // ref to SimCanvas imperative handle

  const API = 'http://localhost:8000';

  async function handleSolve(params) {
    setLoading(true); setError(''); setSimData(null); setPlaying(false);
    try {
      const res  = await fetch(`${API}/api/physics/solve`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setSimData(data);
    } catch(e) { setError(e.message); }
    finally    { setLoading(false); }
  }

  function handleRestart() {
    // Tell SimCanvas to reset clock + snap objects — does NOT touch camera angle
    setPlaying(false);
    canvasRef.current?.restart();
    setTimeout(() => setPlaying(true), 60);
  }

  const steps  = buildSteps(simData);
  const accent = accentFor(simData?.problem_type);

  return (
    <div style={{width:'100%',height:'100vh',display:'flex',flexDirection:'column',
      background:'#0a0a0f',color:'#fff',fontFamily:"'Inter',sans-serif"}}>

      {/* Header */}
      <div style={{padding:'12px 24px',borderBottom:'1px solid #1e1e2e',
        display:'flex',alignItems:'center',gap:'14px',flexShrink:0}}>
        <span style={{fontSize:22}}>⚡</span>
        <div>
          <h1 style={{margin:0,fontSize:18,fontWeight:700,color:'#f59e0b'}}>Physics Engine</h1>
          <p  style={{margin:0,fontSize:11,color:'#555'}}>Mechanics · Thermodynamics · Electromagnetism · Optics · Waves · Modern</p>
        </div>
        {simData&&(
          <div style={{marginLeft:'auto',display:'flex',gap:8,alignItems:'center'}}>
            <span style={{padding:'3px 10px',borderRadius:20,fontSize:11,fontWeight:700,
              background:`${accent}20`,border:`1px solid ${accent}55`,color:accent}}>
              {simData.problem_type?.replace(/_/g,' ').toUpperCase()}
            </span>
            <button onClick={()=>setPlaying(!playing)} style={{
              padding:'7px 18px',borderRadius:8,fontSize:13,fontWeight:600,cursor:'pointer',
              background:playing?'#ef444422':'#f59e0b22',
              border:`1px solid ${playing?'#ef4444':'#f59e0b'}`,
              color:playing?'#ef4444':'#f59e0b'}}>
              {playing?'⏸ Pause':'▶ Play'}
            </button>
            <button onClick={handleRestart} style={{
              padding:'7px 14px',borderRadius:8,fontSize:13,cursor:'pointer',
              background:'#1a1a2a',border:'1px solid #2a2a3a',color:'#aaa'}}>
              ↺ Restart
            </button>
          </div>
        )}
      </div>

      {/* Body */}
      <div style={{flex:1,display:'flex',overflow:'hidden'}}>

        {/* Left: problem input */}
        <div style={{width:340,minWidth:340,borderRight:'1px solid #1e1e2e',overflowY:'auto',padding:16}}>
          <ProblemPanel onSolve={handleSolve} loading={loading} simData={simData}/>
          {error&&(
            <div style={{marginTop:12,padding:'10px 14px',background:'#ff444422',
              border:'1px solid #ff4444',borderRadius:8,color:'#ff6666',fontSize:13}}>
              ⚠ {error}
            </div>
          )}
        </div>

        {/* Centre: 3D canvas — NOTE: no key={} here, so no remount on restart */}
        <div style={{flex:1,position:'relative',minWidth:0}}>
          <SimCanvas
            ref={canvasRef}
            simData={simData}
            playing={playing}
            loading={loading}
          />
        </div>

        {/* Right: step-by-step solution — only when solved */}
        {simData&&steps.length>0&&(
          <div style={{width:290,minWidth:290,borderLeft:'1px solid #1e1e2e',
            overflowY:'auto',background:'#0a0a0f',display:'flex',flexDirection:'column'}}>

            {/* Panel header */}
            <div style={{padding:'12px 16px',borderBottom:'1px solid #1e1e2e',
              background:'#0d0d18',flexShrink:0}}>
              <div style={{color:accent,fontWeight:700,fontSize:13}}>📖 Step-by-Step Solution</div>
              {simData.description&&(
                <div style={{marginTop:6,fontSize:11,color:'#666',fontStyle:'italic',lineHeight:1.5}}>
                  {simData.description}
                </div>
              )}
            </div>

            {/* Steps */}
            <div style={{padding:'10px 12px',display:'flex',flexDirection:'column',gap:6,flex:1}}>
              {steps.map((step,i)=>(
                <div key={i} style={{display:'flex',gap:10,padding:'10px 12px',
                  borderRadius:8,background:i%2===0?'#0d0d18':'transparent',
                  border:'1px solid #111'}}>
                  <div style={{fontSize:16,flexShrink:0,width:28,height:28,
                    display:'flex',alignItems:'center',justifyContent:'center',
                    background:`${accent}18`,borderRadius:6}}>
                    {step.icon}
                  </div>
                  <div style={{flex:1,minWidth:0}}>
                    <div style={{color:accent,fontSize:10,fontWeight:700,
                      letterSpacing:'0.05em',marginBottom:3,textTransform:'uppercase'}}>
                      {step.head}
                    </div>
                    <div style={{color:'#bbb',fontSize:12,lineHeight:1.65,
                      whiteSpace:'pre-line',wordBreak:'break-word'}}>
                      {step.body}
                    </div>
                  </div>
                </div>
              ))}

              {/* Raw values table at the bottom */}
              <div style={{marginTop:8,borderTop:'1px solid #1e1e2e',paddingTop:10}}>
                <div style={{color:'#333',fontSize:10,fontWeight:700,
                  letterSpacing:'0.08em',marginBottom:6}}>ALL VALUES</div>
                {Object.entries(simData.solution||{}).map(([k,v])=>(
                  <div key={k} style={{display:'flex',justifyContent:'space-between',
                    padding:'3px 0',borderBottom:'1px solid #0d0d0d',gap:8}}>
                    <span style={{color:'#444',fontSize:11,flexShrink:0}}>
                      {k.replace(/_/g,' ')}
                    </span>
                    <span style={{color:accent,fontFamily:'monospace',fontSize:11,
                      fontWeight:700,textAlign:'right',wordBreak:'break-all'}}>
                      {String(v)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
