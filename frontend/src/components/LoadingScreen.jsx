const STEPS = [
  { icon: '🧠', text: 'Extracting concept structure...' },
  { icon: '🔍', text: 'Searching 3D model databases...' },
  { icon: '⚖️', text: 'Ranking by semantic similarity...' },
  { icon: '🎨', text: 'Preparing visualization...' },
];

export function LoadingScreen({ message }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '60px 20px',
      gap: 24,
    }}>
      {/* Animated spinner */}
      <div style={{ position: 'relative', width: 64, height: 64 }}>
        <div style={{
          width: 64, height: 64,
          border: '4px solid #21262d',
          borderTop: '4px solid #4EA8DE',
          borderRadius: '50%',
          animation: 'spin 0.9s linear infinite',
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%,-50%)',
          fontSize: 22,
        }}>🌐</div>
      </div>

      <p style={{ color: '#4EA8DE', fontSize: 16, fontWeight: 500 }}>
        {message || 'Searching for the best 3D match...'}
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, width: '100%', maxWidth: 360 }}>
        {STEPS.map((s, i) => (
          <div key={i} style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 16px',
            background: '#161b22',
            border: '1px solid #30363d',
            borderRadius: 10,
            color: '#8b949e',
            fontSize: 13,
            animation: `fadeIn 0.4s ease ${i * 0.3}s both`,
          }}>
            <span>{s.icon}</span>
            <span>{s.text}</span>
          </div>
        ))}
      </div>
      <style>{`@keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }`}</style>
    </div>
  );
}
