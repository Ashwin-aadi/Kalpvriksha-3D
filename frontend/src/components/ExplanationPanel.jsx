export function ExplanationPanel({ concept, result, fallback }) {
  if (!concept && !result) return null;

  const conf = result?.confidence ?? fallback?.model?.confidence;
  const matched = result?.matched_parts ?? fallback?.model?.matched_parts ?? [];
  const missing = result?.missing_parts ?? fallback?.model?.missing_parts ?? [];
  const confColor = conf >= 70 ? '#2ECC71' : conf >= 40 ? '#F39C12' : '#E74C3C';

  return (
    <div style={{
      padding: 20,
      background: '#161b22',
      borderRadius: 16,
      border: '1px solid #30363d',
      display: 'flex',
      flexDirection: 'column',
      gap: 16,
    }}>
      <h3 style={{ color: '#4EA8DE', margin: 0, fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span>🤖</span> AI Explanation
      </h3>

      {concept && (
        <div>
          <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 6 }}>DETECTED CONCEPT</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <span style={{
              background: 'rgba(78,168,222,0.15)',
              border: '1px solid rgba(78,168,222,0.3)',
              padding: '3px 12px',
              borderRadius: 20,
              fontSize: 13,
              color: '#4EA8DE',
            }}>
              {concept.category}
            </span>
            <span style={{
              background: 'rgba(233,113,50,0.15)',
              border: '1px solid rgba(233,113,50,0.3)',
              padding: '3px 12px',
              borderRadius: 20,
              fontSize: 13,
              color: '#E97132',
            }}>
              {concept.type}
            </span>
          </div>
        </div>
      )}

      {concept?.spatial_description && (
        <div>
          <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 6 }}>3D DESCRIPTION</div>
          <p style={{ color: '#c9d1d9', fontSize: 13, margin: 0, lineHeight: 1.5 }}>
            {concept.spatial_description}
          </p>
        </div>
      )}

      {conf !== undefined && (
        <div>
          <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 6 }}>CONFIDENCE SCORE</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 32, fontWeight: 'bold', color: confColor }}>
              {conf?.toFixed(1)}%
            </span>
            <div style={{ flex: 1, height: 8, background: '#21262d', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                width: `${conf}%`,
                background: confColor,
                borderRadius: 4,
                transition: 'width 0.8s ease',
              }} />
            </div>
          </div>
        </div>
      )}

      {matched.length > 0 && (
        <div>
          <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 6 }}>✅ MATCHED COMPONENTS</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {matched.map(m => (
              <span key={m} style={{
                background: 'rgba(46,204,113,0.15)',
                border: '1px solid rgba(46,204,113,0.3)',
                color: '#2ECC71',
                padding: '2px 10px',
                borderRadius: 20,
                fontSize: 12,
              }}>{m}</span>
            ))}
          </div>
        </div>
      )}

      {missing.length > 0 && (
        <div>
          <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 6 }}>⚠️ MISSING COMPONENTS</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {missing.map(m => (
              <span key={m} style={{
                background: 'rgba(243,156,18,0.15)',
                border: '1px solid rgba(243,156,18,0.3)',
                color: '#F39C12',
                padding: '2px 10px',
                borderRadius: 20,
                fontSize: 12,
              }}>{m}</span>
            ))}
          </div>
        </div>
      )}

      {fallback?.explanation && (
        <div style={{
          padding: 12,
          background: 'rgba(78,168,222,0.08)',
          border: '1px solid rgba(78,168,222,0.2)',
          borderRadius: 10,
          fontSize: 13,
          color: '#8b949e',
          lineHeight: 1.6,
        }}>
          {fallback.explanation}
        </div>
      )}

      {concept?.search_keywords && (
        <div>
          <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 6 }}>SEARCH KEYWORDS</div>
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {concept.search_keywords.map(k => (
              <span key={k} style={{
                background: '#21262d',
                color: '#8b949e',
                padding: '2px 8px',
                borderRadius: 20,
                fontSize: 11,
                border: '1px solid #30363d',
              }}>{k}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
