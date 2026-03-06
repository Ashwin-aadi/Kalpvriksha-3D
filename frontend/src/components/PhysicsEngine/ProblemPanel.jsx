import { useState } from 'react';

const CHAPTERS = [
  { id: 'mechanics',        label: '⚙️ Mechanics',         color: '#f59e0b' },
  { id: 'thermodynamics',   label: '🌡️ Thermodynamics',    color: '#ef4444' },
  { id: 'electromagnetism', label: '⚡ Electromagnetism',  color: '#3b82f6' },
  { id: 'optics',           label: '🔭 Optics',            color: '#8b5cf6' },
  { id: 'waves',            label: '〰️ Waves',             color: '#10b981' },
];

const EXAMPLES = {
  mechanics: [
    { label: 'Projectile', text: 'A ball is thrown at 45 degrees with initial velocity 20 m/s from height 0. Find the trajectory.' },
    { label: 'Pendulum',   text: 'A pendulum of length 2 meters swings with initial angle 30 degrees. Simulate the motion.' },
    { label: 'Free fall',  text: 'An object falls from height 100 meters. Show the fall with velocity and acceleration vectors.' },
    { label: 'Truck+Bullet', text: 'A bullet is fired at 300 m/s from a truck moving at 30 m/s. Show relative motion.' },
  ],
  thermodynamics: [
    { label: 'PV diagram',   text: 'Show isothermal, adiabatic, and isochoric processes on a PV diagram.' },
    { label: 'Carnot cycle', text: 'Simulate a Carnot heat engine cycle with T_hot=500K and T_cold=300K.' },
  ],
  electromagnetism: [
    { label: 'Electric field',  text: 'Show the electric field lines of two opposite charges separated by 2 meters.' },
    { label: 'Magnetic force',  text: 'A proton moves at 1e6 m/s through a magnetic field of 0.5 Tesla. Show the circular motion.' },
  ],
  optics: [
    { label: 'Refraction', text: 'Show light refracting from air to glass (n=1.5) at 30 degrees incidence angle.' },
    { label: 'Lens',       text: 'Show image formation by a convex lens with focal length 10cm and object at 25cm.' },
  ],
  waves: [
    { label: 'Superposition', text: 'Show superposition of two waves with frequencies 2Hz and 3Hz.' },
    { label: 'Standing wave',  text: 'Show a standing wave on a string fixed at both ends with L=1m.' },
  ],
};

export function ProblemPanel({ onSolve, loading, simData }) {
  const [chapter, setChapter] = useState('mechanics');
  const [problem, setProblem] = useState('A ball is thrown at 45 degrees with initial velocity 20 m/s. Find the trajectory and range.');
  const currentColor = CHAPTERS.find(c => c.id === chapter)?.color || '#f59e0b';

  const inputStyle = {
    width: '100%', padding: '8px 12px',
    background: '#0f0f1a', border: '1px solid #2a2a3a',
    borderRadius: '8px', color: '#fff', fontSize: '13px',
    boxSizing: 'border-box',
  };
  const labelStyle = { fontSize: '11px', color: '#888', marginBottom: '6px', display: 'block' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Chapter selector */}
      <div>
        <span style={labelStyle}>SELECT CHAPTER</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {CHAPTERS.map(ch => (
            <button key={ch.id} onClick={() => setChapter(ch.id)} style={{
              padding: '8px 14px', borderRadius: '8px', fontSize: '13px',
              cursor: 'pointer', textAlign: 'left', fontWeight: chapter === ch.id ? 700 : 400,
              background: chapter === ch.id ? `${ch.color}18` : '#0f0f1a',
              border: `1px solid ${chapter === ch.id ? ch.color : '#2a2a3a'}`,
              color: chapter === ch.id ? ch.color : '#aaa',
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
          style={{ ...inputStyle, resize: 'vertical', lineHeight: '1.5' }}
          placeholder="Describe the physics problem in natural language..."
        />
        <div style={{ fontSize: '11px', color: '#555', marginTop: '4px' }}>
          Be specific with values — units, angles, velocities, masses
        </div>
      </div>

      {/* Solve button */}
      <button
        onClick={() => onSolve({ chapter, problem })}
        disabled={loading}
        style={{
          padding: '12px', borderRadius: '10px',
          background: loading ? '#1a1a2a' : `linear-gradient(135deg, ${currentColor}, ${currentColor}aa)`,
          border: 'none', color: '#fff', fontSize: '14px', fontWeight: 700,
          cursor: loading ? 'not-allowed' : 'pointer', width: '100%',
        }}
      >
        {loading ? '⏳ Solving...' : '⚡ Solve & Animate'}
      </button>

      {/* Examples */}
      <div>
        <span style={labelStyle}>EXAMPLES</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {(EXAMPLES[chapter] || []).map(ex => (
            <button key={ex.label} onClick={() => setProblem(ex.text)} style={{
              padding: '6px 12px', borderRadius: '6px', fontSize: '12px',
              background: '#0f0f1a', border: '1px solid #2a2a3a',
              color: '#aaa', cursor: 'pointer', textAlign: 'left',
            }}>
              {ex.label}
            </button>
          ))}
        </div>
      </div>

      {/* Solution summary */}
      {simData?.solution && (
        <div style={{
          borderTop: '1px solid #1e1e2e', paddingTop: '16px',
        }}>
          <span style={labelStyle}>SOLUTION</span>
          <div style={{
            background: '#0f0f1a', border: '1px solid #2a2a3a',
            borderRadius: '8px', padding: '12px',
          }}>
            {Object.entries(simData.solution).map(([k, v]) => (
              <div key={k} style={{
                display: 'flex', justifyContent: 'space-between',
                marginBottom: '6px', fontSize: '13px',
              }}>
                <span style={{ color: '#888' }}>{k.replace(/_/g, ' ')}</span>
                <span style={{ color: currentColor, fontFamily: 'monospace', fontWeight: 600 }}>
                  {typeof v === 'number' ? v.toFixed(4) : String(v)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
