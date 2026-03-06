const LAYERS = {
  1: { bg: 'rgba(26,82,118,0.9)',   border: '#1A5276', label: 'Layer 1: Semantic Nearest',    icon: '🔍' },
  2: { bg: 'rgba(26,122,175,0.9)',  border: '#1A7AAF', label: 'Layer 2: Procedural Geometry', icon: '⚙️' },
  3: { bg: 'rgba(22,160,133,0.9)',  border: '#16A085', label: 'Layer 3: Conceptual Metaphor', icon: '🧠' },
  4: { bg: 'rgba(125,60,152,0.9)',  border: '#7D3C98', label: 'Layer 4: Image-to-3D',         icon: '🖼️' },
  0: { bg: 'rgba(100,100,100,0.5)', border: '#666',    label: 'No Match Found',               icon: '❓' },
};

export function FallbackBadge({ layerUsed }) {
  if (layerUsed === undefined || layerUsed === null) return null;
  const { bg, border, label, icon } = LAYERS[layerUsed] || LAYERS[1];
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 7,
      background: bg, border: `1px solid ${border}`,
      color: '#fff', padding: '6px 16px', borderRadius: 20,
      fontSize: 13, fontWeight: 600, backdropFilter: 'blur(8px)',
      fontFamily: 'Inter, sans-serif', boxShadow: `0 2px 12px ${border}44`,
    }}>
      <span>{icon}</span>
      <span>{label}</span>
    </div>
  );
}
