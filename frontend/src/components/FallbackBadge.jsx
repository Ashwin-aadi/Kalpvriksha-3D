const LAYERS = {
  1: { bg: 'rgba(26,82,118,0.8)', border: '#1A5276', label: '⬡ Layer 1: Semantic Nearest' },
  2: { bg: 'rgba(26,122,175,0.8)', border: '#1A7AAF', label: '⬡ Layer 2: Procedural Geometry' },
  3: { bg: 'rgba(22,160,133,0.8)', border: '#16A085', label: '⬡ Layer 3: Conceptual Metaphor' },
  4: { bg: 'rgba(125,60,152,0.8)', border: '#7D3C98', label: '⬡ Layer 4: Image-to-3D' },
  0: { bg: 'rgba(100,100,100,0.5)', border: '#666', label: '⬡ No Match Found' },
};

export function FallbackBadge({ layerUsed }) {
  if (layerUsed === undefined || layerUsed === null) return null;
  const { bg, border, label } = LAYERS[layerUsed] || LAYERS[1];
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      background: bg,
      border: `1px solid ${border}`,
      color: '#fff',
      padding: '5px 14px',
      borderRadius: 20,
      fontSize: 12,
      fontWeight: 600,
      backdropFilter: 'blur(4px)',
    }}>
      {label}
    </div>
  );
}
