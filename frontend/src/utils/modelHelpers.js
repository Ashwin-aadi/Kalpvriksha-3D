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
  const layers = {
    1: { label: 'Semantic Nearest',    color: '#1A5276', icon: '🔍' },
    2: { label: 'Procedural Geometry', color: '#1A7AAF', icon: '⚙️' },
    3: { label: 'Conceptual Metaphor', color: '#16A085', icon: '🧠' },
    4: { label: 'Image-to-3D',         color: '#7D3C98', icon: '🖼️' },
  };
  return layers[layerUsed] || { label: 'Direct Match', color: '#156082', icon: '✅' };
}

export function confidenceColor(score) {
  if (score >= 70) return '#2ECC71';
  if (score >= 40) return '#F39C12';
  return '#E74C3C';
}

export function getBoundingRadius(shapes) {
  if (!shapes?.length) return 5;
  let maxDist = 0;
  for (const s of shapes) {
    const dist = Math.sqrt(s.position[0]**2 + s.position[1]**2 + s.position[2]**2);
    maxDist = Math.max(maxDist, dist);
  }
  return Math.max(5, maxDist + 2);
}
