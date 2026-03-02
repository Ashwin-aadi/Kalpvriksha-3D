export function getCentroid(shapes) {
  if (!shapes?.length) return [0, 0, 0];
  const s = shapes.reduce((a, sh) => ({
    x: a.x + sh.position[0],
    y: a.y + sh.position[1],
    z: a.z + sh.position[2],
  }), { x: 0, y: 0, z: 0 });
  return [s.x / shapes.length, s.y / shapes.length, s.z / shapes.length];
}

export function getLayerInfo(layerUsed) {
  return {
    1: { label: 'Semantic Nearest', color: '#1A5276' },
    2: { label: 'Procedural Geometry', color: '#1A7AAF' },
    3: { label: 'Conceptual Metaphor', color: '#16A085' },
    4: { label: 'Image-to-3D', color: '#7D3C98' },
  }[layerUsed] || { label: 'Direct Match', color: '#156082' };
}

export function confidenceColor(score) {
  return score >= 70 ? '#2ECC71' : score >= 40 ? '#F39C12' : '#E74C3C';
}
