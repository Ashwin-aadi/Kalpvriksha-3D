import { useModelLoader } from '../hooks/useModelLoader';
import { SearchBar }       from '../components/SearchBar';
import { Viewer3D }        from '../components/Viewer3D';
import { ExplanationPanel } from '../components/ExplanationPanel';
import { FallbackBadge }   from '../components/FallbackBadge';
import { LoadingScreen }   from '../components/LoadingScreen';

const GLOBAL_STYLES = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0d1117; font-family: 'Inter', sans-serif; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #131c2e; }
  ::-webkit-scrollbar-thumb { background: #2d3f5a; border-radius: 3px; }
  @keyframes fadeInUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:none; } }
  @keyframes shimmer { 0%,100% { opacity:0.4; } 50% { opacity:0.8; } }
`;

export function Home() {
  const { status, concept, models, fallback, error, step, search, reset } = useModelLoader();
  const top      = models[0] || null;
  const geometry = fallback?.geometry || null;

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #0a0f1a 0%, #0d1117 40%, #080e18 100%)',
      color: '#e6edf3',
    }}>
      <style>{GLOBAL_STYLES}</style>

      {/* Hero header */}
      <header style={{
        padding: '40px 40px 0',
        maxWidth: 1400,
        margin: '0 auto',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 36,
        }}>
          <div>
            <h1 style={{
              fontSize: 32,
              fontWeight: 800,
              background: 'linear-gradient(135deg, #4EA8DE, #0F9ED5, #156082)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '-0.5px',
              lineHeight: 1.2,
            }}>
              Kalpaviraksh-3D
            </h1>
            <p style={{ color: '#4a5568', fontSize: 14, marginTop: 4, fontWeight: 400 }}>
              Semantic 3D Concept Retrieval & Generation System
            </p>
          </div>

          {/* System badges */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            {[
              { icon: '⚡', label: 'Groq Powered', color: '#2ECC71' },
              { icon: '🎯', label: '4-Layer Fallback', color: '#4EA8DE' },
              { icon: '🔮', label: 'LLM Geometry', color: '#9B59B6' },
            ].map(({ icon, label, color }) => (
              <div key={label} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                background: '#0d1117', border: `1px solid ${color}44`,
                color: color, padding: '5px 12px', borderRadius: 20,
                fontSize: 12, fontWeight: 500,
              }}>
                <span>{icon}</span><span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Search section */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingBottom: 32,
        }}>
          <p style={{
            color: '#8b949e', fontSize: 15, marginBottom: 20,
            textAlign: 'center', maxWidth: 600,
          }}>
            Type any concept — data structure, molecule, physics phenomenon, or abstract idea.
            Get an instant 3D visualization.
          </p>
          <SearchBar onSearch={search} isLoading={status === 'loading'} onReset={reset} />
        </div>
      </header>

      {/* Main content */}
      <main style={{ maxWidth: 1400, margin: '0 auto', padding: '0 40px 60px' }}>

        {/* Loading state */}
        {status === 'loading' && <LoadingScreen step={step} />}

        {/* Success state */}
        {status === 'success' && (concept || fallback) && (
          <div style={{ animation: 'fadeInUp 0.5s ease' }}>
            {/* Status bar */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              marginBottom: 16,
              padding: '12px 16px',
              background: '#0d1117',
              border: '1px solid #2d3f5a',
              borderRadius: 12,
            }}>
              {fallback && <FallbackBadge layerUsed={fallback.layer_used} />}
              {top && !fallback && (
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: 7,
                  background: 'rgba(46,204,113,0.1)', border: '1px solid #2ECC71',
                  color: '#2ECC71', padding: '6px 16px', borderRadius: 20, fontSize: 13, fontWeight: 600,
                }}>
                  ✅ Direct Model Match
                </div>
              )}
              <span style={{ color: '#8b949e', fontSize: 13 }}>
                Results for: <strong style={{ color: '#e6edf3' }}>"{concept?.query}"</strong>
              </span>
              <button
                onClick={reset}
                style={{
                  marginLeft: 'auto', background: 'transparent', border: '1px solid #2d3f5a',
                  color: '#8b949e', padding: '4px 12px', borderRadius: 8, cursor: 'pointer',
                  fontSize: 12, fontFamily: 'Inter, sans-serif',
                }}
              >
                New Search
              </button>
            </div>

            {/* 2-column layout */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 360px',
              gap: 20,
              alignItems: 'start',
            }}>
              <Viewer3D
                 modelUrl={top?.embed_url || top?.viewer_url}
                 geometry={geometry}
                 isSketchfab={!!(top?.is_sketchfab && top?.embed_url)}/>
              <ExplanationPanel concept={concept} result={top} fallback={fallback} />
            </div>

            {/* Multiple models list (when direct match found) */}
            {models.length > 1 && (
              <div style={{ marginTop: 20 }}>
                <h3 style={{ color: '#8b949e', fontSize: 14, marginBottom: 12, fontWeight: 500 }}>
                  Other Matches
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px,1fr))', gap: 12 }}>
                  {models.slice(1, 5).map(m => (
                    <div key={m.id} style={{
                      background: '#0d1117', border: '1px solid #2d3f5a', borderRadius: 10,
                      padding: '12px 14px', cursor: 'pointer',
                    }}>
                      <div style={{ color: '#e6edf3', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{m.title}</div>
                      <div style={{ color: '#4EA8DE', fontSize: 12 }}>{m.confidence.toFixed(1)}% match</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error state */}
        {status === 'error' && (
          <div style={{
            marginTop: 24, padding: 24,
            background: 'rgba(231,76,60,0.1)', border: '1px solid #E74C3C',
            borderRadius: 12, animation: 'fadeInUp 0.3s ease',
          }}>
            <h3 style={{ color: '#E74C3C', marginBottom: 8 }}>⚠️ Error</h3>
            <p style={{ color: '#8b949e', fontSize: 14 }}>{error}</p>
            <p style={{ color: '#4a5568', fontSize: 13, marginTop: 8 }}>
              Make sure the backend is running: <code style={{ color: '#4EA8DE' }}>uvicorn app.main:app --reload --port 8000</code>
            </p>
          </div>
        )}

        {/* Idle state — feature showcase */}
        {status === 'idle' && (
          <div style={{ marginTop: 32 }}>
            {/* 4 layer cards */}
            <h2 style={{ color: '#4a5568', fontSize: 14, textAlign: 'center',
                         marginBottom: 20, fontWeight: 500, letterSpacing: '1px',
                         textTransform: 'uppercase' }}>
              4-Layer Fallback System
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 40 }}>
              {[
                { layer: 1, icon: '🔍', title: 'Semantic Match', desc: 'Finds nearest model from Sketchfab & local index using cosine similarity', color: '#1A5276' },
                { layer: 2, icon: '⚙️', title: 'Procedural Gen', desc: 'Rule-based + LLM-powered geometry for 50+ concept types. Handles glucose, DNA, circuits', color: '#1A7AAF' },
                { layer: 3, icon: '🧠', title: 'Conceptual Viz', desc: 'Abstract concepts get symbolic metaphors: hub-spoke, hierarchy, flow diagrams', color: '#16A085' },
                { layer: 4, icon: '🖼️', title: 'Image-to-3D', desc: 'Fetches Wikipedia image and uses Luma AI to reconstruct a 3D model', color: '#7D3C98' },
              ].map(({ layer, icon, title, desc, color }) => (
                <div key={layer} style={{
                  background: '#0d1117', border: `1px solid ${color}55`,
                  borderRadius: 12, padding: 18,
                  borderTop: `3px solid ${color}`,
                  animation: `shimmer 3s ease ${layer * 0.3}s infinite`,
                }}>
                  <div style={{ fontSize: 24, marginBottom: 10 }}>{icon}</div>
                  <div style={{ color: '#e6edf3', fontWeight: 600, fontSize: 14, marginBottom: 6 }}>
                    Layer {layer}: {title}
                  </div>
                  <div style={{ color: '#4a5568', fontSize: 12, lineHeight: 1.5 }}>{desc}</div>
                </div>
              ))}
            </div>

            {/* Example concepts grid */}
            <h2 style={{ color: '#4a5568', fontSize: 14, textAlign: 'center',
                         marginBottom: 20, fontWeight: 500, letterSpacing: '1px',
                         textTransform: 'uppercase' }}>
              Try These Examples
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px,1fr))', gap: 10 }}>
              {[
                { icon: '🧬', name: 'DNA Double Helix', type: 'biological' },
                { icon: '🌌', name: 'Solar System', type: 'physical' },
                { icon: '🌑', name: 'Black Hole', type: 'physical' },
                { icon: '🍬', name: 'Glucose', type: 'chemical' },
                { icon: '🧱', name: 'Binary Search Tree', type: 'algorithmic' },
                { icon: '🧠', name: 'Neural Network', type: 'algorithmic' },
                { icon: '⚖️', name: 'Democracy', type: 'abstract' },
                { icon: '📐', name: 'Inclined Plane', type: 'physics' },
                { icon: '💻', name: 'CPU Architecture', type: 'physical' },
                { icon: '🧫', name: 'Cell Biology', type: 'biological' },
                { icon: '⚛️', name: 'Atom', type: 'physical' },
                { icon: '📊', name: 'Stack', type: 'algorithmic' },
              ].map(({ icon, name, type }) => (
                <button
                  key={name}
                  onClick={() => search(name)}
                  style={{
                    background: '#0d1117', border: '1px solid #2d3f5a', borderRadius: 10,
                    padding: '14px 16px', cursor: 'pointer', textAlign: 'left',
                    transition: 'all 0.15s', fontFamily: 'Inter, sans-serif',
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = '#4EA8DE'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = '#2d3f5a'}
                >
                  <div style={{ fontSize: 22, marginBottom: 6 }}>{icon}</div>
                  <div style={{ color: '#e6edf3', fontSize: 13, fontWeight: 600 }}>{name}</div>
                  <div style={{ color: '#4a5568', fontSize: 11, marginTop: 2 }}>{type}</div>
                </button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
