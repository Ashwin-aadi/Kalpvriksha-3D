import { useEffect, useRef } from 'react';

export function GraphCanvas2D({ plotData, loading }) {
  const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !plotData) return;
        const ctx = canvas.getContext('2d');
        // Use actual displayed size for correct aspect ratio
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        const W = canvas.width;
        const H = canvas.height;
        ctx.clearRect(0, 0, W, H);

    // Background
    ctx.fillStyle = '#070710';
    ctx.fillRect(0, 0, W, H);

    const { plot_type, points } = plotData;
    if (!points || points.length === 0) return;

    // Find data bounds
const xs = points.map(p => p[0]);
const ys = points.map(p => p[1]);
const minX = Math.min(...xs), maxX = Math.max(...xs);
const minY = Math.min(...ys), maxY = Math.max(...ys);
const padX = (maxX - minX) * 0.15 || 1;
const padY = (maxY - minY) * 0.15 || 1;

// Force equal aspect ratio
const dataW = (maxX - minX) + 2 * padX;
const dataH = (maxY - minY) + 2 * padY;
const scale = Math.min(W / dataW, H / dataH);
const offsetX = (W - dataW * scale) / 2;
const offsetY = (H - dataH * scale) / 2;

const toCanvas = (x, y) => ({
  cx: offsetX + (x - minX + padX) * scale,
  cy: H - offsetY - (y - minY + padY) * scale,
});
    // Draw grid
    ctx.strokeStyle = '#1a1a2a';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 10; i++) {
      const x = minX - padX + (i / 10) * (maxX - minX + 2*padX);
      const { cx } = toCanvas(x, 0);
      ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, H); ctx.stroke();
    }
    for (let i = 0; i <= 10; i++) {
      const y = minY - padY + (i / 10) * (maxY - minY + 2*padY);
      const { cy } = toCanvas(0, y);
      ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(W, cy); ctx.stroke();
    }

    // Draw axes
    ctx.strokeStyle = '#333355';
    ctx.lineWidth = 1.5;
    const { cx: x0 } = toCanvas(0, 0);
    const { cy: y0 } = toCanvas(0, 0);
    ctx.beginPath(); ctx.moveTo(x0, 0); ctx.lineTo(x0, H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, y0); ctx.lineTo(W, y0); ctx.stroke();

    // Axis labels
    ctx.fillStyle = '#555577';
    ctx.font = '11px monospace';
    ctx.fillText('x', W - 15, y0 - 5);
    ctx.fillText('y', x0 + 5, 15);

    if (plot_type === 'curve') {
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2;
      // Marching squares returns pairs of segment endpoints — draw each pair separately
      for (let i = 0; i + 1 < points.length; i += 2) {
        const { cx: x1, cy: y1 } = toCanvas(points[i][0], points[i][1]);
        const { cx: x2, cy: y2 } = toCanvas(points[i+1][0], points[i+1][1]);
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }}
    else if (plot_type === 'surface') {
      // For surface in 2D: draw as heatmap using x,z (top-down view)
      const zs = points.map(p => p[2] ?? p[1]);
      const minZ = Math.min(...zs), maxZ = Math.max(...zs);
      const ptSize = Math.max(2, W / Math.sqrt(points.length));
      for (const p of points) {
        const t = maxZ === minZ ? 0.5 : (p[2] - minZ) / (maxZ - minZ);
        const hue = (1 - t) * 240;
        ctx.fillStyle = `hsla(${hue}, 100%, 55%, 0.8)`;
        const { cx, cy } = toCanvas(p[0], p[2] ?? p[1]);
        ctx.fillRect(cx - ptSize/2, cy - ptSize/2, ptSize, ptSize);
      }

    } else if (plot_type === 'vector_field') {
      for (const { origin, direction } of points) {
        const { cx, cy } = toCanvas(origin[0], origin[2] ?? origin[1]);
        const scale = 20;
        const ex = cx + direction[0] * scale;
        const ey = cy - direction[1] * scale;
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(ex, ey); ctx.stroke();
        // Arrowhead
        const angle = Math.atan2(ey - cy, ex - cx);
        ctx.beginPath();
        ctx.moveTo(ex, ey);
        ctx.lineTo(ex - 8*Math.cos(angle-0.4), ey - 8*Math.sin(angle-0.4));
        ctx.lineTo(ex - 8*Math.cos(angle+0.4), ey - 8*Math.sin(angle+0.4));
        ctx.closePath();
        ctx.fillStyle = '#f59e0b';
        ctx.fill();
      }
    }

  }, [plotData]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: '#070710' }}>
      <canvas
  ref={canvasRef}
  style={{ width: '100%', height: '100%', display: 'block' }}
/>
      {loading && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
          justifyContent: 'center', background: 'rgba(7,7,16,0.75)',
          fontSize: '15px', color: '#10b981',
        }}>⏳ Computing graph...</div>
      )}
      {!plotData && !loading && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          color: '#1a1a2a', pointerEvents: 'none', gap: '10px',
        }}>
          <div style={{ fontSize: '48px', opacity: 0.2 }}>📈</div>
          <div style={{ fontSize: '14px', color: '#222' }}>Enter an equation and click Plot</div>
        </div>
      )}
    </div>
  );
}