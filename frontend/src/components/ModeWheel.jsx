import { useState } from 'react';

const MODES = [
  { id: 'concept', label: 'Concept Explorer', icon: '🔭', color: '#6366f1' },
  { id: 'math',    label: 'Math Grapher',     icon: '📐', color: '#10b981' },
  { id: 'physics', label: 'Physics Engine',   icon: '⚡', color: '#f59e0b' },
];

export function ModeWheel({ currentMode, onModeChange }) {
  const [open, setOpen] = useState(false);
  const current = MODES.find(m => m.id === currentMode);

  return (
    <div style={{
      position: 'fixed', bottom: '32px', left: '32px', zIndex: 1000,
    }}>
      {/* Mode options — shown when open */}
      {open && (
        <div style={{ marginBottom: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {MODES.filter(m => m.id !== currentMode).map(mode => (
            <button
              key={mode.id}
              onClick={() => { onModeChange(mode.id); setOpen(false); }}
              style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                background: 'rgba(15,15,25,0.95)',
                border: `1px solid ${mode.color}44`,
                borderRadius: '12px',
                padding: '10px 16px',
                color: '#fff',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                backdropFilter: 'blur(12px)',
                transition: 'all 0.2s',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={e => e.currentTarget.style.borderColor = mode.color}
              onMouseLeave={e => e.currentTarget.style.borderColor = `${mode.color}44`}
            >
              <span style={{ fontSize: '18px' }}>{mode.icon}</span>
              <span style={{ color: mode.color }}>{mode.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* Main toggle button */}
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '56px', height: '56px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${current.color}33, rgba(15,15,25,0.95))`,
          border: `2px solid ${current.color}`,
          color: '#fff',
          fontSize: '22px',
          cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: `0 0 20px ${current.color}55`,
          transition: 'all 0.3s',
          transform: open ? 'rotate(45deg)' : 'rotate(0deg)',
        }}
        title={`Current: ${current.label} — click to switch`}
      >
        {open ? '✕' : current.icon}
      </button>

      {/* Current mode label */}
      {!open && (
        <div style={{
          position: 'absolute', left: '64px', bottom: '14px',
          background: 'rgba(15,15,25,0.85)',
          border: `1px solid ${current.color}33`,
          borderRadius: '8px',
          padding: '4px 10px',
          color: current.color,
          fontSize: '12px',
          fontWeight: 600,
          whiteSpace: 'nowrap',
          backdropFilter: 'blur(8px)',
          pointerEvents: 'none',
        }}>
          {current.label}
        </div>
      )}
    </div>
  );
}
