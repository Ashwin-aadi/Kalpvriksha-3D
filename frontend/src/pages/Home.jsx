import { useModelLoader } from '../hooks/useModelLoader';
import { SearchBar } from '../components/SearchBar';
import { Viewer3D } from '../components/Viewer3D';
import { ExplanationPanel } from '../components/ExplanationPanel';
import { FallbackBadge } from '../components/FallbackBadge';
import { LoadingScreen } from '../components/LoadingScreen';

export function Home() {
  const { status, concept, models, fallback, error, search, reset } = useModelLoader();

  const top = models[0] || null;
  const geometry = fallback?.geometry || null;
  const modelUrl = top?.viewer_url || null;
  const hasResult = status === 'success';

  return (
    <div style={{ minHeight: '100vh', background: '#0d1117', color: '#e6edf3' }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid #21262d',
        padding: '16px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        background: 'rgba(13,17,23,0.95)',
        backdropFilter: 'blur(10px)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 28 }}>🌐</span>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#e6edf3' }}>
              Kalpaviraksh-3D
            </h1>
            <p style={{ margin: 0, fontSize: 11, color: '#8b949e' }}>
              Semantic 3D Concept Retrieval & Generation
            </p>
          </div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            style={{
              padding: '6px 14px',
              background: '#21262d',
              border: '1px solid #30363d',
              borderRadius: 8,
              color: '#8b949e',
              textDecoration: 'none',
              fontSize: 12,
            }}
          >
            📋 API Docs
          </a>
        </div>
      </header>

      <main style={{ maxWidth: 1280, margin: '0 auto', padding: '32px 24px' }}>
        {/* Hero section */}
        {status === 'idle' && (
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <h2 style={{ fontSize: 36, fontWeight: 800, marginBottom: 12, background: 'linear-gradient(135deg, #4EA8DE, #0F9ED5)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Find the 3D Model for Any Concept
            </h2>
            <p style={{ color: '#8b949e', fontSize: 16, maxWidth: 560, margin: '0 auto 8px' }}>
              Type any natural language concept — physical objects, biological structures,
              mathematical ideas, or abstract notions. The system finds, validates, or generates
              the best possible 3D representation.
            </p>
            <div style={{ display: 'flex', gap: 24, justifyContent: 'center', marginTop: 20, flexWrap: 'wrap' }}>
              {[
                { icon: '🔬', label: 'Biological structures' },
                { icon: '🏗️', label: 'Physical objects' },
                { icon: '💡', label: 'Abstract concepts' },
                { icon: '⚙️', label: 'Algorithms & data structures' },
              ].map(({ icon, label }) => (
                <div key={label} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 16px',
                  background: '#161b22',
                  border: '1px solid #30363d',
                  borderRadius: 20,
                  color: '#8b949e',
                  fontSize: 13,
                }}>
                  <span>{icon}</span> {label}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Search bar */}
        <div style={{ maxWidth: 800, margin: '0 auto 32px', position: 'relative', zIndex: 10 }}>
          <SearchBar
            onSearch={search}
            onReset={reset}
            isLoading={status === 'loading'}
            hasResult={hasResult || status === 'error'}
          />
        </div>

        {/* Loading state */}
        {status === 'loading' && <LoadingScreen />}

        {/* Error state */}
        {status === 'error' && (
          <div style={{
            maxWidth: 600,
            margin: '0 auto',
            padding: 24,
            background: 'rgba(231,76,60,0.1)',
            border: '1px solid rgba(231,76,60,0.3)',
            borderRadius: 16,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>⚠️</div>
            <h3 style={{ color: '#E74C3C', marginBottom: 8 }}>Connection Error</h3>
            <p style={{ color: '#8b949e', fontSize: 14 }}>{error}</p>
            <p style={{ color: '#8b949e', fontSize: 12, marginTop: 8 }}>
              Make sure the backend is running: <code style={{ color: '#4EA8DE' }}>uvicorn app.main:app --reload --port 8000</code>
            </p>
          </div>
        )}

        {/* Success state */}
        {status === 'success' && (
          <div>
            {/* Result header */}
            {concept && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
                <h2 style={{ margin: 0, fontSize: 22, color: '#e6edf3' }}>
                  Results for <span style={{ color: '#4EA8DE' }}>"{concept.query}"</span>
                </h2>
                {fallback && (
                  <FallbackBadge layerUsed={fallback.layer_used} />
                )}
                {top && (
                  <span style={{
                    padding: '4px 12px',
                    background: 'rgba(46,204,113,0.15)',
                    border: '1px solid rgba(46,204,113,0.3)',
                    borderRadius: 20,
                    color: '#2ECC71',
                    fontSize: 12,
                    fontWeight: 600,
                  }}>
                    ✓ Direct Match Found
                  </span>
                )}
              </div>
            )}

            {/* Main layout grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1fr) 360px',
              gap: 24,
              alignItems: 'start',
            }}>
              {/* Left: 3D Viewer */}
              <div>
                <Viewer3D modelUrl={modelUrl} geometry={geometry} />
                <p style={{ color: '#8b949e', fontSize: 12, textAlign: 'center', marginTop: 8 }}>
                  🖱️ Drag to rotate · Scroll to zoom · Right-click to pan
                </p>
              </div>

              {/* Right: Explanation Panel */}
              <ExplanationPanel
                concept={concept}
                result={top}
                fallback={fallback}
              />
            </div>

            {/* Multiple models carousel if more than 1 */}
            {models.length > 1 && (
              <div style={{ marginTop: 24 }}>
                <h3 style={{ color: '#8b949e', fontSize: 14, marginBottom: 12 }}>OTHER MATCHES</h3>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  {models.slice(1, 5).map(m => (
                    <div key={m.id} style={{
                      padding: '12px 16px',
                      background: '#161b22',
                      border: '1px solid #30363d',
                      borderRadius: 12,
                      minWidth: 200,
                    }}>
                      <div style={{ color: '#e6edf3', fontSize: 14, fontWeight: 600, marginBottom: 4 }}>{m.title}</div>
                      <div style={{ color: '#8b949e', fontSize: 12 }}>Confidence: {m.confidence.toFixed(1)}%</div>
                      <div style={{ color: '#8b949e', fontSize: 11 }}>Source: {m.source}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Idle empty state placeholder viewer */}
        {status === 'idle' && (
          <div style={{ maxWidth: 700, margin: '0 auto' }}>
            <Viewer3D modelUrl={null} geometry={null} />
            <p style={{ color: '#8b949e', fontSize: 12, textAlign: 'center', marginTop: 8 }}>
              Enter a concept above to begin exploring
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid #21262d',
        padding: '16px 24px',
        textAlign: 'center',
        color: '#8b949e',
        fontSize: 12,
        marginTop: 64,
      }}>
        Kalpaviraksh-3D · Team: Ashwin · Ashutosh · Anushree · Vaishnavi
        <span style={{ margin: '0 8px' }}>·</span>
        4-Layer Fallback System · Powered by FastAPI + React + Three.js
      </footer>
    </div>
  );
}
