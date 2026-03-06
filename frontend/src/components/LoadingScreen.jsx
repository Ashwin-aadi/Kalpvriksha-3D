import { useEffect, useState } from 'react';

const STEPS = [
  { icon: '🧠', text: 'Extracting concept structure...' },
  { icon: '🔍', text: 'Searching 3D model databases...' },
  { icon: '⚖️', text: 'Ranking by semantic similarity...' },
  { icon: '🎨', text: 'Preparing visualization...' },
];

export function LoadingScreen({ step }) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (!step) return;
    const idx = STEPS.findIndex(s => s.text === step);
    if (idx !== -1) setActiveStep(idx);
  }, [step]);

  // Auto-progress if no specific step given
  useEffect(() => {
    if (step) return;
    const timer = setInterval(() => {
      setActiveStep(s => (s + 1) % STEPS.length);
    }, 900);
    return () => clearInterval(timer);
  }, [step]);

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      padding: '60px 20px', gap: 28,
      background: '#0d1117', borderRadius: 16,
      border: '1px solid #2d3f5a', marginTop: 24,
    }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100% { opacity:0.6; } 50% { opacity:1; } }
        @keyframes slideIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:none; } }
      `}</style>

      {/* Spinner */}
      <div style={{ position: 'relative', width: 72, height: 72 }}>
        <div style={{
          width: 72, height: 72,
          border: '3px solid #1a2332',
          borderTop: '3px solid #4EA8DE',
          borderRight: '3px solid #0F9ED5',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
          position: 'absolute',
        }} />
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%,-50%)', fontSize: 26,
          animation: 'pulse 1.5s ease infinite',
        }}>🔮</div>
      </div>

      <p style={{
        color: '#4EA8DE', fontSize: 17, fontWeight: 600,
        fontFamily: 'Inter, sans-serif', margin: 0,
        animation: 'pulse 2s ease infinite',
      }}>
        {step || 'Searching for the best 3D match...'}
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, width: '100%', maxWidth: 400 }}>
        {STEPS.map((s, i) => (
          <div key={i} style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '11px 16px',
            background: i === activeStep ? '#131c2e' : 'rgba(13,17,23,0.4)',
            border: `1px solid ${i === activeStep ? '#4EA8DE' : '#2d3f5a'}`,
            borderRadius: 10,
            color: i === activeStep ? '#e6edf3' : '#4a5568',
            fontSize: 13,
            fontFamily: 'Inter, sans-serif',
            transition: 'all 0.3s ease',
            animation: `slideIn 0.4s ease ${i * 0.15}s both`,
          }}>
            <span style={{ fontSize: 18 }}>{s.icon}</span>
            <span>{s.text}</span>
            {i < activeStep && <span style={{ marginLeft: 'auto', color: '#2ECC71' }}>✓</span>}
            {i === activeStep && (
              <div style={{
                marginLeft: 'auto', width: 16, height: 16,
                border: '2px solid #4EA8DE', borderTop: '2px solid transparent',
                borderRadius: '50%', animation: 'spin 0.6s linear infinite',
              }} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
