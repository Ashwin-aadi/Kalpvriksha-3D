import { useState } from 'react';
import { GraphCanvas } from './GraphCanvas.jsx';
import { EquationPanel } from './EquationPanel.jsx';

export function MathGrapher() {
  const [plotData, setPlotData]   = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);

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
        <div>
          <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 700, color: '#10b981' }}>
            Math Grapher
          </h1>
          <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
            3D Cartesian · Cylindrical · Spherical — equations, vectors, analysis
          </p>
        </div>
      </div>

      {/* Body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left panel */}
        <div style={{
          width: '340px', minWidth: '340px',
          borderRight: '1px solid #1e1e2e',
          overflowY: 'auto',
          padding: '20px',
        }}>
          <EquationPanel
            onPlot={handlePlot}
            onAnalyze={handleAnalyze}
            loading={loading}
            analysisResult={analysisResult}
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

        {/* 3D Canvas */}
        <div style={{ flex: 1, position: 'relative' }}>
          <GraphCanvas plotData={plotData} loading={loading} />
        </div>
      </div>
    </div>
  );
}
