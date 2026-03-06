import { useState } from 'react';

const CHAPTERS = [
  { id: 'mechanics',        label: '⚙️ Mechanics',         color: '#f59e0b' },
  { id: 'thermodynamics',   label: '🌡️ Thermodynamics',    color: '#ef4444' },
  { id: 'electromagnetism', label: '⚡ Electromagnetism',  color: '#3b82f6' },
  { id: 'waves',            label: '〰️ Waves',             color: '#10b981' },
  { id: 'optics',           label: '🔭 Optics',            color: '#8b5cf6' },
];

const EXAMPLES = {
  mechanics: [
    { label: 'Projectile',       text: 'A ball is thrown at 45 degrees with initial velocity 20 m/s from height 0. Find the trajectory and range.' },
    { label: 'Free Fall',        text: 'An object is dropped from height 80 meters. Find the time to fall and final velocity.' },
    { label: 'Pendulum',         text: 'A pendulum of length 2 meters is released from 30 degrees. Simulate the oscillation.' },
    { label: 'Circular Motion',  text: 'A mass of 0.5 kg moves in a vertical circle of radius 1 meter. What is the minimum speed at the bottom to complete the circle?' },
    { label: 'Spring SHM',       text: 'A spring with k=50 N/m has a mass of 2 kg attached. Amplitude is 0.3 m. Show the oscillation.' },
    { label: 'Elastic Collision',text: 'Mass m1=3kg moving at 6 m/s collides elastically with m2=1kg at rest. Find final velocities.' },
    { label: 'Truck + Bullet',   text: 'A bullet is fired at 300 m/s relative to a truck moving at 30 m/s. Show the relative motion.' },
  ],
  thermodynamics: [
    { label: 'Isothermal',  text: 'Show an isothermal expansion from V=1L at P=101325 Pa and T=300K.' },
    { label: 'Adiabatic',   text: 'Show an adiabatic expansion from V=0.001 m³ at P=200000 Pa with gamma=1.4.' },
    { label: 'Carnot Cycle',text: 'A Carnot engine operates between T_hot=600K and T_cold=300K with Q_hot=2000J. Find efficiency and work.' },
    { label: 'Isobaric',    text: 'Show an isobaric process at P=101325 Pa from V=1L to V=3L.' },
  ],
  electromagnetism: [
    { label: 'Opposite Charges', text: 'Show the electric field between two opposite point charges of 2 μC separated by 3 meters.' },
    { label: 'Same Charges',     text: 'Show the electric field of two positive charges of 1 μC separated by 2 meters.' },
    { label: 'Magnetic Circular',text: 'A proton moves at 1×10⁶ m/s through a magnetic field of 0.1 Tesla. Show the circular motion.' },
    { label: 'Electron Orbit',   text: 'An electron with charge 1.6×10⁻¹⁹ C and mass 9.1×10⁻³¹ kg moves at 2×10⁶ m/s in B=0.5T field.' },
  ],
  waves: [
    { label: 'Beat Frequency',  text: 'Show superposition of two waves with frequencies 5 Hz and 7 Hz, both amplitude 1.' },
    { label: 'Resonance',       text: 'Show superposition of two waves with equal frequency 4 Hz and same amplitude 2.' },
    { label: 'Standing Wave',   text: 'Show a standing wave on a string of length 0.5 m with fundamental frequency 200 Hz and 3 harmonics.' },
    { label: 'Interference',    text: 'Show superposition of f1=3Hz A1=2 and f2=5Hz A2=1 for 4 seconds.' },
  ],
  optics: [
    { label: 'Convex Lens',     text: 'Object placed 25 cm from a convex lens of focal length 10 cm. Find image position and magnification.' },
    { label: 'Concave Lens',    text: 'Object placed 20 cm from a concave lens of focal length 15 cm. Find the virtual image.' },
    { label: 'Refraction Air→Glass', text: 'Light travels from air (n=1) to glass (n=1.5) at 40 degree incidence angle. Find refraction angle.' },
    { label: 'Total Internal Reflection', text: 'Light travels from glass (n=1.5) to air (n=1) at 50 degree incidence angle.' },
  ],
};

export function ProblemPanel({ onSolve, loading, simData }) {
  const [chapter, setChapter] = useState('mechanics');
  const [problem, setProblem] = useState('A ball is thrown at 45 degrees with initial velocity 20 m/s from height 0. Find the trajectory and range.');
  const currentColor = CHAPTERS.find(c => c.id === chapter)?.color || '#f59e0b';

  const inputStyle = {
    width: '100%', padding: '8px 12px',
    background: '#0f0f1a', border: '1px solid #2a2a3a',
    borderRadius: '8px', color: '#fff', fontSize: '13px',
    boxSizing: 'border-box',
  };
  const labelStyle = { fontSize: '11px', color: '#888', marginBottom: '6px', display: 'block', letterSpacing: '0.05em' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

      {/* Chapter selector */}
      <div>
        <span style={labelStyle}>SELECT CHAPTER</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          {CHAPTERS.map(ch => (
            <button key={ch.id} onClick={() => {
              setChapter(ch.id);
              // Set first example as default problem
              if (EXAMPLES[ch.id]?.[0]) setProblem(EXAMPLES[ch.id][0].text);
            }} style={{
              padding: '8px 14px', borderRadius: '8px', fontSize: '13px',
              cursor: 'pointer', textAlign: 'left',
              fontWeight: chapter === ch.id ? 700 : 400,
              background: chapter === ch.id ? `${ch.color}18` : '#0f0f1a',
              border: `1px solid ${chapter === ch.id ? ch.color : '#2a2a3a'}`,
              color: chapter === ch.id ? ch.color : '#aaa',
              transition: 'all 0.15s',
            }}>{ch.label}</button>
          ))}
        </div>
      </div>

      {/* Problem input */}
      <div>
        <span style={labelStyle}>DESCRIBE THE PROBLEM</span>
        <textarea
          value={problem}
          onChange={e => setProblem(e.target.value)}
          rows={5}
          style={{ ...inputStyle, resize: 'vertical', lineHeight: '1.5', fontFamily: 'inherit' }}
          placeholder="Describe the physics problem in plain English..."
        />
        <div style={{ fontSize: '11px', color: '#444', marginTop: '4px' }}>
          Include specific values — units, angles, masses, velocities
        </div>
      </div>

      {/* Solve button */}
      <button
        onClick={() => onSolve({ chapter, problem })}
        disabled={loading}
        style={{
          padding: '12px', borderRadius: '10px',
          background: loading
            ? '#1a1a2a'
            : `linear-gradient(135deg, ${currentColor}cc, ${currentColor}88)`,
          border: `1px solid ${loading ? '#2a2a3a' : currentColor}`,
          color: '#fff', fontSize: '14px', fontWeight: 700,
          cursor: loading ? 'not-allowed' : 'pointer',
          width: '100%', transition: 'all 0.2s',
        }}
      >
        {loading ? '⏳ Solving...' : '⚡ Solve & Animate'}
      </button>

      {/* Examples */}
      <div>
        <span style={labelStyle}>QUICK EXAMPLES</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          {(EXAMPLES[chapter] || []).map(ex => (
            <button key={ex.label} onClick={() => setProblem(ex.text)} style={{
              padding: '6px 12px', borderRadius: '6px', fontSize: '12px',
              background: '#0f0f1a',
              border: `1px solid ${problem === ex.text ? currentColor + '66' : '#2a2a3a'}`,
              color: problem === ex.text ? currentColor : '#888',
              cursor: 'pointer', textAlign: 'left',
              transition: 'all 0.15s',
            }}>
              {ex.label}
            </button>
          ))}
        </div>
      </div>

      {/* Solution summary */}
      {simData?.solution && (
        <div style={{ borderTop: '1px solid #1e1e2e', paddingTop: '16px' }}>
          <span style={labelStyle}>SOLUTION</span>
          <div style={{
            background: '#0f0f1a', border: `1px solid ${currentColor}22`,
            borderRadius: '8px', padding: '12px',
          }}>
            {simData.problem_type && (
              <div style={{ fontSize: '11px', color: currentColor, marginBottom: '8px', fontWeight: 700 }}>
                {simData.problem_type.replace(/_/g, ' ').toUpperCase()}
              </div>
            )}
            {Object.entries(simData.solution).map(([k, v]) => (
              <div key={k} style={{
                display: 'flex', justifyContent: 'space-between',
                marginBottom: '5px', fontSize: '12px',
                borderBottom: '1px solid #1a1a2a', paddingBottom: '4px',
              }}>
                <span style={{ color: '#666' }}>{k.replace(/_/g, ' ')}</span>
                <span style={{ color: currentColor, fontFamily: 'monospace', fontWeight: 600 }}>
                  {String(v)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
