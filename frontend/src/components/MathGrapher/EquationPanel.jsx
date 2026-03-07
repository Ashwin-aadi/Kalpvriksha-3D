import { useState } from 'react';

const COORD_SYSTEMS = [
  { id: 'cartesian',   label: 'Cartesian',   hint: 'z = sin(x) * cos(y)' },
  { id: 'cylindrical', label: 'Cylindrical', hint: 'z = r * sin(theta)' },
  { id: 'spherical',   label: 'Spherical',   hint: 'rho = 2 * sin(phi)' },
  { id: 'parametric',  label: 'Parametric',  hint: 'x=cos(t), y=sin(t), z=t' },
  { id: 'vector',      label: 'Vector Field', hint: 'F = [-y, x, 0]' },
  { id: 'implicit', label: 'Implicit', hint: 'x**2 + y**2 + z**2 - 1' },
];

const EXAMPLES = [
  { label: 'Paraboloid',   eq: 'z = x**2 + y**2',         coord: 'cartesian' },
  { label: 'Saddle',       eq: 'z = x**2 - y**2',         coord: 'cartesian' },
  { label: 'Sine surface', eq: 'z = sin(x) * cos(y)',      coord: 'cartesian' },
  { label: 'Sphere',       eq: 'rho = 1',                  coord: 'spherical' },
  { label: 'Cone',         eq: 'z = r',                    coord: 'cylindrical' },
  { label: 'Helix',        eq: 'x=cos(t), y=sin(t), z=t/3', coord: 'parametric' },
  { label: 'Vortex field', eq: 'F = [-y, x, 0]',          coord: 'vector' },
  { label: 'Sphere',       eq: 'x**2 + y**2 + z**2 - 1',      coord: 'implicit' },
  { label: 'Hyperboloid',  eq: 'x**2 + y**2 - z**2 - 1',      coord: 'implicit' },
  { label: 'Torus',        eq: '(sqrt(x**2+y**2)-2)**2+z**2-1', coord: 'implicit' },
];

export function EquationPanel({ onPlot, onAnalyze, loading, analysisResult }) {
  const [coord, setCoord]       = useState('cartesian');
  const [equation, setEquation] = useState('z = x**2 + y**2');
  const [resolution, setRes]    = useState(40);
  const [xRange, setXRange]     = useState('[-5, 5]');
  const [yRange, setYRange]     = useState('[-5, 5]');
  const [analyzeType, setAnalyzeType] = useState('slope');
  const [analyzePoint, setAnalyzePoint] = useState('0, 0');
  const [showAnalysis, setShowAnalysis] = useState(false);

  function handlePlot() {
    onPlot({
      equation, coord_system: coord,
      resolution: parseInt(resolution),
      x_range: JSON.parse(xRange),
      y_range: JSON.parse(yRange),
    });
  }

  function handleAnalyze() {
    const [px, py] = analyzePoint.split(',').map(s => parseFloat(s.trim()));
    onAnalyze({
      equation, coord_system: coord,
      analysis_type: analyzeType,
      point: [px, py],
      x_range: JSON.parse(xRange),
      y_range: JSON.parse(yRange),
    });
  }

  function loadExample(ex) {
    setEquation(ex.eq);
    setCoord(ex.coord);
  }

  const green = '#10b981';
  const inputStyle = {
    width: '100%', padding: '8px 12px',
    background: '#0f0f1a', border: '1px solid #2a2a3a',
    borderRadius: '8px', color: '#fff', fontSize: '13px',
    fontFamily: 'monospace', boxSizing: 'border-box',
  };
  const labelStyle = { fontSize: '11px', color: '#888', marginBottom: '4px', display: 'block' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Coordinate system */}
      <div>
        <span style={labelStyle}>COORDINATE SYSTEM</span>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {COORD_SYSTEMS.map(cs => (
            <button key={cs.id} onClick={() => setCoord(cs.id)} style={{
              padding: '5px 10px', borderRadius: '6px', fontSize: '12px',
              cursor: 'pointer', fontWeight: coord === cs.id ? 700 : 400,
              background: coord === cs.id ? `${green}22` : '#0f0f1a',
              border: `1px solid ${coord === cs.id ? green : '#2a2a3a'}`,
              color: coord === cs.id ? green : '#aaa',
            }}>{cs.label}</button>
          ))}
        </div>
      </div>

      {/* Equation input */}
      <div>
        <span style={labelStyle}>EQUATION</span>
        <textarea
          value={equation}
          onChange={e => setEquation(e.target.value)}
          rows={3}
          style={{ ...inputStyle, resize: 'vertical' }}
          placeholder={COORD_SYSTEMS.find(c => c.id === coord)?.hint}
        />
        <div style={{ fontSize: '11px', color: '#555', marginTop: '4px' }}>
          Use: **, sin(), cos(), tan(), exp(), log(), sqrt(), pi, e
        </div>
      </div>

      {/* Range inputs */}
      {(coord === 'cartesian' || coord === 'cylindrical') && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <div>
            <span style={labelStyle}>X RANGE</span>
            <input value={xRange} onChange={e => setXRange(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <span style={labelStyle}>Y RANGE</span>
            <input value={yRange} onChange={e => setYRange(e.target.value)} style={inputStyle} />
          </div>
        </div>
      )}

      {/* Resolution */}
      <div>
        <span style={labelStyle}>RESOLUTION: {resolution}×{resolution}</span>
        <input type="range" min={10} max={80} value={resolution}
          onChange={e => setRes(e.target.value)}
          style={{ width: '100%', accentColor: green }} />
      </div>

      {/* Plot button */}
      <button onClick={handlePlot} disabled={loading} style={{
        padding: '12px', borderRadius: '10px',
        background: loading ? '#1a1a2a' : `linear-gradient(135deg, ${green}, #059669)`,
        border: 'none', color: '#fff', fontSize: '14px', fontWeight: 700,
        cursor: loading ? 'not-allowed' : 'pointer', width: '100%',
      }}>
        {loading ? '⏳ Plotting...' : '📐 Plot Graph'}
      </button>

      {/* Examples */}
      <div>
        <span style={labelStyle}>QUICK EXAMPLES</span>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {EXAMPLES.map(ex => (
            <button key={ex.label} onClick={() => loadExample(ex)} style={{
              padding: '4px 10px', borderRadius: '6px', fontSize: '11px',
              background: '#0f0f1a', border: '1px solid #2a2a3a',
              color: '#aaa', cursor: 'pointer',
            }}>{ex.label}</button>
          ))}
        </div>
      </div>

      {/* Analysis section */}
      <div style={{ borderTop: '1px solid #1e1e2e', paddingTop: '16px' }}>
        <button onClick={() => setShowAnalysis(!showAnalysis)} style={{
          background: 'none', border: 'none', color: '#f59e0b',
          cursor: 'pointer', fontSize: '13px', fontWeight: 600, padding: 0,
        }}>
          {showAnalysis ? '▼' : '▶'} Analysis Tools
        </button>

        {showAnalysis && (
          <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div>
              <span style={labelStyle}>ANALYSIS TYPE</span>
              <select value={analyzeType} onChange={e => setAnalyzeType(e.target.value)} style={inputStyle}>
                <option value="slope">Slope / Gradient at point</option>
                <option value="area">Area under curve</option>
                <option value="divergence">Divergence (vector field)</option>
                <option value="curl">Curl (vector field)</option>
              </select>
            </div>
            <div>
              <span style={labelStyle}>POINT (x, y)</span>
              <input value={analyzePoint} onChange={e => setAnalyzePoint(e.target.value)} style={inputStyle} placeholder="0, 0" />
            </div>
            <button onClick={handleAnalyze} disabled={loading} style={{
              padding: '10px', borderRadius: '8px',
              background: '#f59e0b22', border: '1px solid #f59e0b',
              color: '#f59e0b', fontSize: '13px', fontWeight: 600,
              cursor: 'pointer',
            }}>
              🔍 Analyze
            </button>

            {analysisResult && (
              <div style={{
                background: '#0f0f1a', border: '1px solid #2a2a3a',
                borderRadius: '8px', padding: '12px', fontSize: '13px',
              }}>
                <div style={{ color: '#f59e0b', fontWeight: 700, marginBottom: '6px' }}>
                  {analysisResult.type}
                </div>
                {Object.entries(analysisResult).filter(([k]) => k !== 'type').map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ color: '#888' }}>{k}</span>
                    <span style={{ color: '#fff', fontFamily: 'monospace' }}>
                      {typeof v === 'number' ? v.toFixed(6) : JSON.stringify(v)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
