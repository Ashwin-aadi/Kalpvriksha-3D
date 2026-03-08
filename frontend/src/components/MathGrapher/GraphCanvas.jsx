import { useEffect, useRef } from 'react';
import * as THREE from 'three';

const DEFAULT_SPH = { theta: Math.PI / 4, phi: Math.PI / 3, radius: 15 };

export function GraphCanvas({ plotData, loading }) {
  const mountRef   = useRef(null);
  const sceneRef   = useRef(null);
  const rendererRef= useRef(null);
  const cameraRef  = useRef(null);
  const frameRef   = useRef(null);
  const spherical  = useRef({ ...DEFAULT_SPH });
  const target     = useRef(new THREE.Vector3(0, 0, 0));
  const isDragging = useRef(false);
  const prevMouse  = useRef({ x: 0, y: 0 });
  const keysHeld   = useRef({});
  const keyLoopRef = useRef(null);

  // ── INIT ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#070710');
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(60, mount.clientWidth / mount.clientHeight, 0.1, 1000);
    cameraRef.current = camera;
    updateCamera();

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const grid = new THREE.GridHelper(20, 20, '#1a1a2a', '#111118');
    grid.material.transparent = true; grid.material.opacity = 0.5;
    scene.add(grid);
    addAxes(scene);
    scene.add(new THREE.AmbientLight('#ffffff', 0.6));
    const dir = new THREE.DirectionalLight('#ffffff', 0.8);
    dir.position.set(10, 20, 10); scene.add(dir);

    // Mouse
    const onDown  = e => { isDragging.current = true; prevMouse.current = { x: e.clientX, y: e.clientY }; };
    const onUp    = () => { isDragging.current = false; };
    const onMove  = e => {
      if (!isDragging.current) return;
      spherical.current.theta -= (e.clientX - prevMouse.current.x) * 0.008;
      spherical.current.phi    = Math.max(0.05, Math.min(Math.PI - 0.05,
        spherical.current.phi - (e.clientY - prevMouse.current.y) * 0.008));
      prevMouse.current = { x: e.clientX, y: e.clientY };
      updateCamera();
    };
    const onWheel = e => {
      e.preventDefault();
      spherical.current.radius = Math.max(1.5, Math.min(60, spherical.current.radius + e.deltaY * 0.025));
      updateCamera();
    };

    // Keyboard
    const onKeyDown = e => {
      if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
      keysHeld.current[e.key.toLowerCase()] = true;
      if (e.key.toLowerCase() === 'r') {
        spherical.current = { ...DEFAULT_SPH };
        target.current.set(0, 0, 0);
        updateCamera();
      }
    };
    const onKeyUp = e => {
      if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
      delete keysHeld.current[e.key.toLowerCase()];
    };
    mount.addEventListener('mousedown', onDown);
    mount.addEventListener('mouseup',   onUp);
    window.addEventListener('mouseup',  onUp);
    mount.addEventListener('mousemove', onMove);
    mount.addEventListener('wheel',     onWheel, { passive: false });
    window.addEventListener('keydown',  onKeyDown);
    window.addEventListener('keyup',    onKeyUp);

    // Key loop — derives forward/right from actual camera vectors so ANY angle works correctly
    const keyLoop = () => {
      const k = keysHeld.current;
      if (Object.keys(k).length === 0) { keyLoopRef.current = requestAnimationFrame(keyLoop); return; }

      const { theta, phi, radius } = spherical.current;
      const spd = radius * 0.025;
      const t = target.current;
      const cam = cameraRef.current;

      // True forward = vector from camera TO target, projected onto XZ plane, then normalized
      // This is always correct regardless of phi or theta
      const camPos = cam.position;
      const fwd = new THREE.Vector3(
        t.x - camPos.x,
        0,              // flatten to horizontal plane for WASD pan
        t.z - camPos.z
      ).normalize();

      // Right = cross product of world-up and forward
      const up  = new THREE.Vector3(0, 1, 0);
      const rgt = new THREE.Vector3().crossVectors(fwd, up).normalize();

      if (k['w'] || k['arrowup'])    { t.x += fwd.x*spd; t.z += fwd.z*spd; }
      if (k['s'] || k['arrowdown'])  { t.x -= fwd.x*spd; t.z -= fwd.z*spd; }
      if (k['a'] || k['arrowleft'])  { t.x -= rgt.x*spd; t.z -= rgt.z*spd; }
      if (k['d'] || k['arrowright']) { t.x += rgt.x*spd; t.z += rgt.z*spd; }
      if (k['e']) { t.y += spd; }
      if (k['q']) { t.y -= spd; }

      updateCamera();
      keyLoopRef.current = requestAnimationFrame(keyLoop);
    };
    keyLoopRef.current = requestAnimationFrame(keyLoop);

    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(frameRef.current);
      cancelAnimationFrame(keyLoopRef.current);
      mount.removeEventListener('mousedown', onDown);
      mount.removeEventListener('mouseup',   onUp);
      window.removeEventListener('mouseup',  onUp);
      mount.removeEventListener('mousemove', onMove);
      mount.removeEventListener('wheel',     onWheel);
      window.removeEventListener('keydown',  onKeyDown);
      window.removeEventListener('keyup',    onKeyUp);
      window.removeEventListener('resize',   onResize);
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, []);

  // ── REBUILD PLOT ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!sceneRef.current || !plotData) return;
    const scene = sceneRef.current;

    scene.children.filter(c => c.userData.isPlot).forEach(c => {
      scene.remove(c);
      if (c.geometry) c.geometry.dispose();
      if (c.material) c.material.dispose();
    });

    const { plot_type, points, triangles } = plotData;

    if (plot_type === 'surface' && points && triangles) {
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(points.flat()), 3));
      geometry.setIndex(triangles.flat());
      geometry.computeVertexNormals();

      // Height-based coloring
      const ys   = points.map(p => p[1]);
      const minY = Math.min(...ys), maxY = Math.max(...ys);
      const cols = new Float32Array(points.length * 3);
      points.forEach((p, i) => {
        const t = maxY === minY ? 0.5 : (p[1] - minY) / (maxY - minY);
        const c = new THREE.Color().setHSL(0.67 - t * 0.67, 1.0, 0.5);
        cols[i*3]=c.r; cols[i*3+1]=c.g; cols[i*3+2]=c.b;
      });
      geometry.setAttribute('color', new THREE.BufferAttribute(cols, 3));

      const mesh = new THREE.Mesh(geometry, new THREE.MeshPhongMaterial({
        vertexColors: true, side: THREE.DoubleSide,
        shininess: 60, transparent: true, opacity: 0.88,
      }));
      mesh.userData.isPlot = true;
      scene.add(mesh);

      const wire = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
        color: '#ffffff', wireframe: true, transparent: true, opacity: 0.06,
      }));
      wire.userData.isPlot = true;
      scene.add(wire);

      // Auto-zoom
      const maxVal = Math.max(...points.flat().map(Math.abs).filter(isFinite));
      if (maxVal > 0) {
        spherical.current.radius = Math.min(50, Math.max(8, maxVal * 2.8));
        updateCamera();
      }

    } else if (plot_type === 'curve' && points) {
      const pts  = points.map(p => new THREE.Vector3(p[0], p[1], p[2] || 0));
      const line = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(pts),
        new THREE.LineBasicMaterial({ color: '#10b981', linewidth: 2 })
      );
      line.userData.isPlot = true;
      scene.add(line);

    } else if (plot_type === 'vector_field' && points) {
      points.forEach(({ origin, direction }) => {
        const dir = new THREE.Vector3(...direction).normalize();
        const arrow = new THREE.ArrowHelper(dir, new THREE.Vector3(...origin), 0.8, '#f59e0b', 0.2, 0.1);
        arrow.userData.isPlot = true;
        scene.add(arrow);
      });
    }
  }, [plotData]);

  function updateCamera() {
    if (!cameraRef.current) return;
    const { theta, phi, radius } = spherical.current;
    const t = target.current;
    cameraRef.current.position.set(
      t.x + radius * Math.sin(phi) * Math.cos(theta),
      t.y + radius * Math.cos(phi),
      t.z + radius * Math.sin(phi) * Math.sin(theta),
    );
    cameraRef.current.lookAt(t);
  }

  return (
    <div ref={mountRef} style={{ width: '100%', height: '100%', position: 'relative' }}>
      {loading && (
        <div style={{
          position:'absolute',inset:0,display:'flex',alignItems:'center',
          justifyContent:'center',background:'rgba(7,7,16,0.75)',zIndex:10,
          fontSize:'15px',color:'#10b981',
        }}>
          ⏳ Computing graph...
        </div>
      )}
      {!plotData && !loading && (
        <div style={{
          position:'absolute',inset:0,display:'flex',flexDirection:'column',
          alignItems:'center',justifyContent:'center',
          color:'#1a1a2a',pointerEvents:'none',gap:'10px',
        }}>
          <div style={{ fontSize:'48px', opacity:0.2 }}>📐</div>
          <div style={{ fontSize:'14px',color:'#222' }}>Enter an equation and click Plot</div>
        </div>
      )}
      {/* Camera hint */}
      <div style={{
        position:'absolute',bottom:'12px',right:'12px',
        background:'rgba(5,5,15,0.7)',border:'1px solid #1a1a2a',
        borderRadius:'7px',padding:'7px 11px',color:'#333',
        fontSize:'10px',lineHeight:'1.8',pointerEvents:'none',
      }}>
        <div style={{color:'#555',fontWeight:700,marginBottom:'3px'}}>CAMERA</div>
        <div>🖱 Drag — orbit &nbsp; ⚲ Scroll — zoom</div>
        <div>
          <kbd style={kbdStyle}>W</kbd><kbd style={kbdStyle}>S</kbd>
          <kbd style={kbdStyle}>A</kbd><kbd style={kbdStyle}>D</kbd> pan &nbsp;
          <kbd style={kbdStyle}>Q</kbd><kbd style={kbdStyle}>E</kbd> up/dn &nbsp;
          <kbd style={kbdStyle}>R</kbd> reset
        </div>
      </div>
    </div>
  );
}

const kbdStyle = {
  background:'#111',border:'1px solid #222',borderRadius:'3px',
  padding:'0 3px',margin:'0 1px',fontSize:'9px',color:'#555',
};

function addAxes(scene) {
  const axes = [
    { dir:[1,0,0], color:'#ef4444', label:'X' },
    { dir:[0,1,0], color:'#22c55e', label:'Y' },
    { dir:[0,0,1], color:'#3b82f6', label:'Z' },
  ];
  axes.forEach(({ dir, color }) => {
    scene.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0,0,0),
        new THREE.Vector3(...dir).multiplyScalar(8),
      ]),
      new THREE.LineBasicMaterial({ color, transparent:true, opacity:0.5 })
    ));
    scene.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0,0,0),
        new THREE.Vector3(...dir).multiplyScalar(-4),
      ]),
      new THREE.LineBasicMaterial({ color, transparent:true, opacity:0.15 })
    ));
  });
}
