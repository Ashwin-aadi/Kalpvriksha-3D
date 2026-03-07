import { useState } from 'react';
import { SimCanvas } from './SimCanvas.jsx';
import { ProblemPanel } from './ProblemPanel.jsx';

export function PhysicsEngine() {
  const [simData, setSimData]   = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [playing, setPlaying]   = useState(false);

  const API = 'http://localhost:8000';

  async function handleSolve(params) {
    setLoading(true);
    setError('');
    setSimData(null);
    setPlaying(false);
    try {
      const res = await fetch(`${API}/api/physics/solve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setSimData(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      width: '100%', height: '100vh',
      display: 'flex', flexDirection: 'column',
      background: '#0a0a0f', color: '#fff',
      fontFamily: "'Inter', sans-serif",
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 32px',
        borderBottom: '1px solid #1e1e2e',
        display: 'flex', alignItems: 'center', gap: '16px',
      }}>
        <span style={{ fontSize: '24px' }}>⚡</span>
        <div>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 700, color: '#f59e0b' }}>
            Physics Engine
          </h1>
          <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
            Mechanics · Thermodynamics · Electromagnetism · Optics · Waves
          </p>
        </div>
        {simData && (
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
            <button onClick={() => setPlaying(!playing)} style={{
              padding: '8px 20px', borderRadius: '8px',
              background: playing ? '#ef444422' : '#f59e0b22',
              border: `1px solid ${playing ? '#ef4444' : '#f59e0b'}`,
              color: playing ? '#ef4444' : '#f59e0b',
              cursor: 'pointer', fontWeight: 600, fontSize: '13px',
            }}>
              {playing ? '⏸ Pause' : '▶ Play'}
            </button>
            <button onClick={() => { setPlaying(false); setTimeout(() => setPlaying(true), 50); }} style={{
              padding: '8px 16px', borderRadius: '8px',
              background: '#1a1a2a', border: '1px solid #2a2a3a',
              color: '#aaa', cursor: 'pointer', fontSize: '13px',
            }}>
              ↺ Restart
            </button>
          </div>
        )}
      </div>

      {/* Body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left panel */}
        <div style={{
          width: '360px', minWidth: '360px',
          borderRight: '1px solid #1e1e2e',
          overflowY: 'auto', padding: '20px',
        }}>
          <ProblemPanel onSolve={handleSolve} loading={loading} simData={simData} />
          {error && (
            <div style={{
              marginTop: '12px', padding: '10px 14px',
              background: '#ff444422', border: '1px solid #ff4444',
              borderRadius: '8px', color: '#ff6666', fontSize: '13px',
            }}>
              ⚠ {error}
            </div>
          )}
        </div>

        {/* Simulation canvas */}
        <div style={{ flex: 1, position: 'relative' }}>
          <SimCanvas simData={simData} playing={playing} loading={loading} />
        </div>
      </div>
    </div>
  );
}
