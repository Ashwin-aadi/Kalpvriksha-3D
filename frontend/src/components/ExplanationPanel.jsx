import { confidenceColor } from '../utils/modelHelpers';

function Tag({ text, type }) {
  const styles = {
    matched:   { bg: 'rgba(46,204,113,0.15)',  border: '#2ECC71', color: '#2ECC71' },
    missing:   { bg: 'rgba(231,76,60,0.12)',   border: '#E74C3C', color: '#E74C3C' },
    component: { bg: 'rgba(78,168,222,0.12)',  border: '#4EA8DE', color: '#4EA8DE' },
    related:   { bg: 'rgba(155,89,182,0.12)',  border: '#9B59B6', color: '#9B59B6' },
  };
  const s = styles[type] || styles.component;
  return (
    <span style={{
      display: 'inline-block', background: s.bg, border: `1px solid ${s.border}`,
      color: s.color, padding: '3px 10px', borderRadius: 20,
      fontSize: 12, fontWeight: 500, margin: '2px 3px',
    }}>{text}</span>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{
        fontSize: 11, fontWeight: 600, color: '#4a5568',
        textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: 8,
      }}>{title}</div>
      {children}
    </div>
  );
}

export function ExplanationPanel({ concept, result, fallback }) {
  if (!concept && !result && !fallback) return null;

  const conf    = result?.confidence ?? fallback?.model?.confidence;
  const matched = result?.matched_parts ?? fallback?.model?.matched_parts ?? [];
  const missing = result?.missing_parts ?? fallback?.model?.missing_parts ?? [];
  const isGeometry = fallback?.geometry != null;

  return (
    <div style={{
      background: '#0d1117', border: '1px solid #2d3f5a', borderRadius: 16,
      padding: 24, display: 'flex', flexDirection: 'column',
      fontFamily: 'Inter, sans-serif', overflowY: 'auto', height: '100%',
    }}>
      <h3 style={{ color: '#e6edf3', margin: '0 0 20px 0', fontSize: 16, fontWeight: 700,
                   display: 'flex', alignItems: 'center', gap: 8 }}>
        <span>🧠</span> AI Analysis
      </h3>

      {concept && (
        <Section title="Detected Concept">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <span style={{ background: 'rgba(78,168,222,0.15)', border: '1px solid #4EA8DE',
                           color: '#4EA8DE', padding: '4px 14px', borderRadius: 20,
                           fontSize: 13, fontWeight: 600 }}>{concept.category}</span>
            <span style={{ background: 'rgba(21,96,130,0.3)', color: '#85C1E9',
                           padding: '4px 10px', borderRadius: 20, fontSize: 12 }}>{concept.type}</span>
          </div>
          {concept.spatial_description && (
            <p style={{ color: '#8b949e', fontSize: 13, margin: '10px 0 0', lineHeight: 1.5 }}>
              {concept.spatial_description}
            </p>
          )}
        </Section>
      )}

      {conf !== undefined && (
        <Section title="Match Confidence">
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span style={{ fontSize: 36, fontWeight: 800, color: confidenceColor(conf), lineHeight: 1 }}>
              {conf?.toFixed(1)}%
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ background: '#1a2332', borderRadius: 4, height: 6, overflow: 'hidden' }}>
                <div style={{
                  width: `${Math.min(conf, 100)}%`, height: '100%',
                  background: `linear-gradient(90deg, ${confidenceColor(conf)}, ${confidenceColor(conf)}88)`,
                  borderRadius: 4, transition: 'width 0.8s ease',
                }} />
              </div>
            </div>
          </div>
        </Section>
      )}

      {concept?.components?.length > 0 && (
        <Section title="Components">
          <div>{concept.components.map(c => <Tag key={c} text={c} type="component" />)}</div>
        </Section>
      )}

      {matched.length > 0 && (
        <Section title="✅ Matched Parts">
          <div>{matched.map(m => <Tag key={m} text={m} type="matched" />)}</div>
        </Section>
      )}
      {missing.length > 0 && (
        <Section title="⚠️ Missing Parts">
          <div>{missing.map(m => <Tag key={m} text={m} type="missing" />)}</div>
        </Section>
      )}

      {fallback?.explanation && (
        <Section title="How It Was Generated">
          <div style={{
            background: '#131c2e', border: '1px solid #2d3f5a', borderRadius: 10,
            padding: '12px 14px', fontSize: 13, color: '#8b949e', lineHeight: 1.6,
          }}>{fallback.explanation}</div>
        </Section>
      )}

      {isGeometry && fallback?.geometry && (
        <Section title="Scene Info">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[
              { label: 'Shapes', value: fallback.geometry.length },
              { label: 'Layer', value: `Layer ${fallback.layer_used}` },
              { label: 'Method', value: fallback.layer_name?.split(' ')[0] },
              { label: 'Type', value: concept?.type || '—' },
            ].map(({ label, value }) => (
              <div key={label} style={{
                background: '#131c2e', border: '1px solid #2d3f5a', borderRadius: 8, padding: '10px 12px',
              }}>
                <div style={{ color: '#4a5568', fontSize: 11, marginBottom: 2 }}>{label}</div>
                <div style={{ color: '#e6edf3', fontSize: 14, fontWeight: 600 }}>{value}</div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {concept?.search_keywords?.length > 0 && (
        <Section title="Keywords">
          <div>{concept.search_keywords.slice(0,6).map(k => <Tag key={k} text={k} type="related" />)}</div>
        </Section>
      )}
    </div>
  );
}
