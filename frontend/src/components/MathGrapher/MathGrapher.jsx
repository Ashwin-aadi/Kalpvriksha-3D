import { useState } from 'react';
import { GraphCanvas } from './GraphCanvas.jsx';
import { GraphCanvas2D } from './GraphCanvas2D.jsx';
import { EquationPanel } from './EquationPanel.jsx';

export function MathGrapher() {
  const [plotData, setPlotData]   = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [mode, setMode]           = useState('3d'); // '2d' or '3d'

  const API = 'http://localhost:8000';

  async function handlePlot(params) {
    setLoading(true);
    setError('');
    setAnalysisResult(null);
    try {
      const res = await fetch(`${API}/api/math/plot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setPlotData(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze(params) {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/math/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setAnalysisResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const green = '#10b981';

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
        <span style={{ fontSize: '24px' }}>📐</span>
        <div style={{ flex: 1 }}>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 700, color: green }}>
            Math Grapher
          </h1>
          <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
            3D Cartesian · Cylindrical · Spherical — equations, vectors, analysis
          </p>
        </div>

        {/* 2D / 3D Toggle */}
        <div style={{
          display: 'flex', background: '#0f0f1a',
          border: '1px solid #2a2a3a', borderRadius: '10px', overflow: 'hidden',
        }}>
          {['2d', '3d'].map(m => (
            <button key={m} onClick={() => setMode(m)} style={{
              padding: '8px 22px', border: 'none', cursor: 'pointer',
              fontWeight: 700, fontSize: '14px', transition: 'all 0.2s',
              background: mode === m ? `${green}22` : 'transparent',
              color: mode === m ? green : '#555',
              borderRight: m === '2d' ? '1px solid #2a2a3a' : 'none',
            }}>{m.toUpperCase()}</button>
          ))}
        </div>
      </div>

      {/* Body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left panel */}
        <div style={{
          width: '340px', minWidth: '340px',
          borderRight: '1px solid #1e1e2e',
          overflowY: 'auto', padding: '20px',
        }}>
          <EquationPanel
            onPlot={handlePlot}
            onAnalyze={handleAnalyze}
            loading={loading}
            analysisResult={analysisResult}
            mode={mode}
          />
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

        {/* Canvas — switches between 2D and 3D */}
        <div style={{ flex: 1, position: 'relative' }}>
          {mode === '3d'
            ? <GraphCanvas plotData={plotData} loading={loading} />
            : <GraphCanvas2D plotData={plotData} loading={loading} />
          }
        </div>
      </div>
    </div>
  );
}