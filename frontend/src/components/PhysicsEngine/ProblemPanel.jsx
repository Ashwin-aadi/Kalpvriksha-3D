import { useState } from 'react';

const CHAPTERS = [
  { id: 'mechanics',        label: '⚙️  Mechanics',         color: '#f59e0b' },
  { id: 'thermodynamics',   label: '🌡️  Thermodynamics',    color: '#ef4444' },
  { id: 'electromagnetism', label: '⚡  Electromagnetism',  color: '#3b82f6' },
  { id: 'waves',            label: '〰️  Waves',             color: '#10b981' },
  { id: 'optics',           label: '🔭  Optics',            color: '#8b5cf6' },
  { id: 'modern_physics',   label: '⚛️  Modern Physics',    color: '#ec4899' },
];

const EXAMPLES = {
  mechanics: [
    { label: 'Projectile',       text: 'A ball is thrown at 60° with v₀=25 m/s from a cliff 20m high. Find trajectory, range, and max height.' },
    { label: 'Free Fall',        text: 'A stone is dropped from 122.5m. Find time to hit ground, final velocity, and KE at impact (mass=0.5kg).' },
    { label: 'Pendulum',         text: 'A pendulum of length 1.5m and mass 0.3kg is released from 45°. Find period, max velocity, and total energy.' },
    { label: 'Vertical Circle',  text: 'A ball of mass 0.2kg moves in vertical circle of radius 0.8m. Find minimum speed at bottom to complete the circle.' },
    { label: 'Spring SHM',       text: 'A spring k=200 N/m has mass 0.5kg attached. Amplitude=0.1m. Find period, max velocity, and max acceleration.' },
    { label: 'Block on Incline', text: 'Block of 3kg on incline of 37°. μs=0.5, μk=0.3. Applied force F=10N up the incline. Does it slide?' },
    { label: 'Atwood Machine',   text: 'Masses m1=4kg and m2=2kg hang over a pulley. Find acceleration and tension in string.' },
    { label: 'Rolling',          text: 'A solid cylinder of mass 2kg and radius 0.1m rolls without slipping down 30° incline. Find acceleration.' },
    { label: 'Rotation',         text: 'A disk of mass 3kg and radius 0.4m has torque 8 N·m applied. Find angular acceleration and KE after 5s.' },
    { label: 'Elastic Collision',text: 'Ball m1=3kg at 8m/s collides elastically with m2=1kg at rest. Find final velocities and check energy.' },
  ],
  thermodynamics: [
    { label: 'Calorimetry',      text: 'Mix 0.5kg water at 80°C (c=4186) with 0.2kg aluminium at 20°C (c=900). Find equilibrium temperature.' },
    { label: 'Isothermal',       text: 'Ideal gas expands isothermally from V=2L at P=4atm and T=300K. Show PV diagram and find work done.' },
    { label: 'Adiabatic',        text: 'Ideal diatomic gas (γ=1.4) expands adiabatically from P=5atm V=1L at T=400K. Find work and final state.' },
    { label: 'Carnot Cycle',     text: 'Carnot engine between T_hot=600K and T_cold=300K absorbs Q_hot=3000J. Find efficiency, work, and heat rejected.' },
    { label: 'Heat Conduction',  text: 'Steel rod k=50 W/m·K, area=1cm², length=0.5m between 200°C and 20°C. Rate of heat transfer?' },
    { label: 'Isobaric',         text: 'Gas at P=2atm expands isobarically from V=1L to V=4L at T=300K. Find work done and heat absorbed.' },
  ],
  electromagnetism: [
    { label: 'Opposite Charges', text: 'Two charges +3μC and -3μC separated by 4m. Draw electric field, find force and potential energy.' },
    { label: 'Same Charges',     text: 'Two charges +2μC each separated by 3m. Find repulsive force and sketch field lines.' },
    { label: 'Proton in B field',text: 'Proton (m=1.67×10⁻²⁷kg, q=1.6×10⁻¹⁹C) moves at 2×10⁶ m/s in B=0.5T. Find radius and period.' },
    { label: 'Electron orbit',   text: 'Electron (m=9.1×10⁻³¹kg, charge=-1.6×10⁻¹⁹C, q_sign=-1) at 3×10⁶m/s in B=0.2T. Show circular motion.' },
    { label: 'LC Circuit',       text: 'LC circuit with L=0.1H, C=100μF charged to V₀=12V. Find frequency, max current, and max charge.' },
    { label: 'Damped LC',        text: 'RLC circuit with L=0.5H, C=50μF, R=10Ω charged to V₀=20V. Show damped oscillation.' },
    { label: 'EM Induction',     text: 'Coil with B=2T, area=0.05m² rotates at ω=100 rad/s in resistance R=50Ω. Find max EMF and current.' },
  ],
  waves: [
    { label: 'Beats',            text: 'Two tuning forks of 440Hz and 444Hz superpose. Find beat frequency and show waveform.' },
    { label: 'Resonance',        text: 'Two waves f=200Hz A=2 and f=200Hz A=1.5 superpose. Show resultant amplitude.' },
    { label: 'Doppler — approach',text: 'Ambulance (f=500Hz) approaches observer at vs=30m/s. v_sound=340m/s. Find observed frequency.' },
    { label: 'Doppler — recede', text: 'Train sounding 600Hz recedes at 40m/s. v_sound=340m/s, observer stationary. Find frequency heard.' },
    { label: 'Interference',     text: 'Waves f1=3Hz A1=2 and f2=5Hz A2=1.5 for duration 4 seconds. Show superposition.' },
  ],
  optics: [
    { label: 'Refraction Air→Glass', text: 'Light from air (n=1) into glass (n=1.5) at 40° incidence. Find refraction angle. Show ray diagram.' },
    { label: 'Total Internal Reflection', text: 'Light from glass (n=1.5) into air at 50° incidence angle. Does TIR occur? Find critical angle.' },
    { label: 'Convex Lens',      text: 'Convex lens f=15cm. Object h=3cm at d=40cm. Find image distance, magnification, and nature. Draw ray diagram.' },
    { label: 'Concave Lens',     text: 'Concave lens f=20cm. Object h=4cm at d=30cm. Locate image and find magnification.' },
    { label: 'Concave Mirror',   text: 'Concave mirror f=10cm. Object at 25cm from pole, h=3cm. Find image and magnification.' },
    { label: 'Prism Deviation',  text: 'Glass prism apex angle 60°, n=1.5. Light enters at 40° incidence. Find deviation and min deviation.' },
    { label: "Young's Double Slit", text: "d=0.5mm, D=1m, λ=589nm. Find fringe width, 3rd bright fringe position, and 2nd dark fringe." },
  ],
  modern_physics: [
    { label: 'Photoelectric',    text: 'Metal work function φ=2.3eV. Light of frequency 8×10¹⁴Hz. Find KE_max, stopping potential, threshold frequency.' },
    { label: 'Below Threshold',  text: 'Sodium work function φ=2.28eV. Light of frequency 5×10¹⁴Hz incident. Does photoelectric emission occur?' },
    { label: 'Hydrogen n=3→1',   text: 'Hydrogen atom (Z=1) electron falls from n=3 to n=1. Find wavelength emitted and series name.' },
    { label: 'He+ Bohr',         text: 'He⁺ ion (Z=2) transition from n=4 to n=2. Find energy emitted and wavelength.' },
    { label: 'Radioactive Decay',text: 'Sample has 1×10⁶ atoms initially. Half-life=10s. Find remaining atoms and activity after 30s.' },
    { label: 'Short Half-life',  text: 'Radioactive element N0=5×10⁸, half_life=2s. How many remain after 8 seconds?' },
  ],
};

export function ProblemPanel({ onSolve, loading, simData }) {
  const [chapter, setChapter] = useState('mechanics');
  const [problem, setProblem] = useState(EXAMPLES.mechanics[0].text);
  const cc = CHAPTERS.find(c => c.id === chapter) || CHAPTERS[0];

  const inputStyle = {
    width:'100%', padding:'9px 12px',
    background:'#0a0a12', border:'1px solid #2a2a3a',
    borderRadius:'8px', color:'#ddd', fontSize:'13px',
    boxSizing:'border-box', fontFamily:'inherit',
  };
  const lbl = { fontSize:'10px', color:'#666', marginBottom:'5px',
                display:'block', letterSpacing:'0.08em', fontWeight:700 };

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:'14px' }}>

      {/* Chapter selector */}
      <div>
        <span style={lbl}>SELECT CHAPTER</span>
        <div style={{ display:'flex', flexDirection:'column', gap:'4px' }}>
          {CHAPTERS.map(ch => (
            <button key={ch.id} onClick={() => {
              setChapter(ch.id);
              if (EXAMPLES[ch.id]?.[0]) setProblem(EXAMPLES[ch.id][0].text);
            }} style={{
              padding:'7px 12px', borderRadius:'7px', fontSize:'12px',
              cursor:'pointer', textAlign:'left',
              fontWeight: chapter===ch.id ? 700 : 400,
              background: chapter===ch.id ? `${ch.color}15` : 'transparent',
              border:`1px solid ${chapter===ch.id ? ch.color : '#1e1e2e'}`,
              color: chapter===ch.id ? ch.color : '#666',
              transition:'all 0.15s',
            }}>{ch.label}</button>
          ))}
        </div>
      </div>

      {/* Problem input */}
      <div>
        <span style={lbl}>PROBLEM STATEMENT</span>
        <textarea
          value={problem}
          onChange={e => setProblem(e.target.value)}
          rows={6}
          style={{...inputStyle, resize:'vertical', lineHeight:'1.6'}}
          placeholder="Describe the physics problem in plain English with all values..."
        />
        <div style={{fontSize:'10px',color:'#333',marginTop:'3px'}}>
          Include all values, units, angles — LLM extracts parameters automatically
        </div>
      </div>

      {/* Solve button */}
      <button
        onClick={() => onSolve({ chapter, problem })}
        disabled={loading}
        style={{
          padding:'13px', borderRadius:'10px',
          background: loading ? '#111' : `linear-gradient(135deg,${cc.color}dd,${cc.color}88)`,
          border:`1px solid ${loading ? '#222' : cc.color}`,
          color:'#fff', fontSize:'14px', fontWeight:700,
          cursor: loading ? 'not-allowed' : 'pointer',
          width:'100%', transition:'all 0.2s',
          boxShadow: loading ? 'none' : `0 4px 20px ${cc.color}33`,
        }}
      >
        {loading ? '⏳  Solving & Animating...' : `⚡  Solve & Animate`}
      </button>

      {/* Examples */}
      <div>
        <span style={lbl}>QUICK EXAMPLES</span>
        <div style={{display:'flex',flexDirection:'column',gap:'4px'}}>
          {(EXAMPLES[chapter]||[]).map(ex => (
            <button key={ex.label} onClick={() => setProblem(ex.text)} style={{
              padding:'6px 10px', borderRadius:'6px', fontSize:'11px',
              background: problem===ex.text ? `${cc.color}12` : 'transparent',
              border:`1px solid ${problem===ex.text ? cc.color+'55' : '#1e1e2e'}`,
              color: problem===ex.text ? cc.color : '#555',
              cursor:'pointer', textAlign:'left', transition:'all 0.12s',
            }}>
              {ex.label}
            </button>
          ))}
        </div>
      </div>

      {/* Solution panel */}
      {simData?.solution && Object.keys(simData.solution).length > 0 && (
        <div style={{ borderTop:'1px solid #111', paddingTop:'14px' }}>
          <div style={{
            display:'flex', justifyContent:'space-between', alignItems:'center',
            marginBottom:'8px',
          }}>
            <span style={lbl}>SOLUTION</span>
            <span style={{
              fontSize:'10px', padding:'2px 8px', borderRadius:'20px',
              background:`${cc.color}20`, color:cc.color, fontWeight:700,
            }}>
              {simData.problem_type?.replace(/_/g,' ').toUpperCase()}
            </span>
          </div>
          <div style={{
            background:'#0a0a12', border:`1px solid ${cc.color}18`,
            borderRadius:'8px', overflow:'hidden',
          }}>
            {Object.entries(simData.solution).map(([k,v],i) => (
              <div key={k} style={{
                display:'flex', justifyContent:'space-between', alignItems:'center',
                padding:'6px 10px',
                background: i%2===0 ? 'transparent' : '#0d0d18',
                borderBottom:'1px solid #0f0f1a',
              }}>
                <span style={{color:'#555',fontSize:'11px',maxWidth:'50%'}}>
                  {k.replace(/_/g,' ')}
                </span>
                <span style={{
                  color: cc.color, fontFamily:'monospace', fontSize:'11px',
                  fontWeight:700, textAlign:'right', maxWidth:'50%', wordBreak:'break-all',
                }}>
                  {String(v)}
                </span>
              </div>
            ))}
          </div>
          {simData.description && (
            <div style={{
              marginTop:'8px', fontSize:'11px', color:'#444', fontStyle:'italic',
            }}>
              {simData.description}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
