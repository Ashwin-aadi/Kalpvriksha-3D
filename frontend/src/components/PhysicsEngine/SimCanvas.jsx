import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

const DEFAULT_SPH = { theta: Math.PI / 4, phi: Math.PI / 3, radius: 22 };
const OPTICS_TYPES = ['ray_refraction', 'lens', 'mirror', 'prism', 'youngs_double', 'single_slit', 'thin_film'];

export function SimCanvas({ simData, playing, loading }) {
  const mountRef    = useRef(null);
  const sceneRef    = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef   = useRef(null);
  const frameRef    = useRef(null);
  const clockRef    = useRef(new THREE.Clock());
  const animRef     = useRef([]);
  const playingRef  = useRef(false);
  const spherical   = useRef({ ...DEFAULT_SPH });
  const target      = useRef(new THREE.Vector3(0, 0, 0));
  const isDragging  = useRef(false);
  const prevMouse   = useRef({ x: 0, y: 0 });
  const keysHeld    = useRef({});
  const labelDivs   = useRef([]);
  const keyLoopRef  = useRef(null);

  playingRef.current = playing;

  const isOptics = simData && OPTICS_TYPES.includes(simData.problem_type);

  // ── INIT ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#080810');
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(55, mount.clientWidth / mount.clientHeight, 0.01, 1000);
    cameraRef.current = camera;
    updateCamera();

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Base scene elements
    const grid = new THREE.GridHelper(40, 40, '#1a1a2a', '#0f0f1a');
    grid.material.transparent = true; grid.material.opacity = 0.4;
    scene.add(grid);
    addAxes(scene);
    scene.add(new THREE.AmbientLight('#ffffff', 0.6));
    const sun = new THREE.DirectionalLight('#ffffff', 1);
    sun.position.set(10, 20, 10); sun.castShadow = true; scene.add(sun);

    // Mouse controls
    const onDown  = e => { isDragging.current = true; prevMouse.current = { x: e.clientX, y: e.clientY }; };
    const onUp    = () => { isDragging.current = false; };
    const onMove  = e => {
      if (!isDragging.current) return;
      spherical.current.theta -= (e.clientX - prevMouse.current.x) * 0.007;
      spherical.current.phi    = Math.max(0.05, Math.min(Math.PI - 0.05,
        spherical.current.phi - (e.clientY - prevMouse.current.y) * 0.007));
      prevMouse.current = { x: e.clientX, y: e.clientY };
      updateCamera();
    };
    const onWheel = e => {
      e.preventDefault();
      spherical.current.radius = Math.max(1.5, Math.min(120, spherical.current.radius + e.deltaY * 0.03));
      updateCamera();
    };

    // Keyboard controls
    const onKeyDown = e => {
      keysHeld.current[e.key.toLowerCase()] = true;
      if (e.key.toLowerCase() === 'r') {
        spherical.current = { ...DEFAULT_SPH };
        target.current.set(0, 0, 0);
        updateCamera();
      }
    };
    const onKeyUp = e => { delete keysHeld.current[e.key.toLowerCase()]; };

    mount.addEventListener('mousedown', onDown);
    mount.addEventListener('mouseup',   onUp);
    window.addEventListener('mouseup',  onUp);
    mount.addEventListener('mousemove', onMove);
    mount.addEventListener('wheel',     onWheel, { passive: false });
    window.addEventListener('keydown',  onKeyDown);
    window.addEventListener('keyup',    onKeyUp);

    // Key movement loop — derives forward/right from actual camera vectors so ANY angle works correctly
    const keyLoop = () => {
      const k = keysHeld.current;
      if (Object.keys(k).length === 0) { keyLoopRef.current = requestAnimationFrame(keyLoop); return; }

      const { radius } = spherical.current;
      const spd = radius * 0.025;
      const t = target.current;
      const cam = cameraRef.current;

      // True forward = vector from camera TO target, flattened to XZ plane
      // Always correct regardless of phi or theta
      const camPos = cam.position;
      const fwd = new THREE.Vector3(
        t.x - camPos.x,
        0,
        t.z - camPos.z
      ).normalize();

      // Right = cross product of forward and world-up
      const up  = new THREE.Vector3(0, 1, 0);
      const rgt = new THREE.Vector3().crossVectors(fwd, up).normalize();

      if (k['w'] || k['arrowup'])    { t.x += fwd.x*spd; t.z += fwd.z*spd; }
      if (k['s'] || k['arrowdown'])  { t.x -= fwd.x*spd; t.z -= fwd.z*spd; }
      if (k['a'] || k['arrowleft'])  { t.x += rgt.x*spd; t.z += rgt.z*spd; }
      if (k['d'] || k['arrowright']) { t.x -= rgt.x*spd; t.z -= rgt.z*spd; }
      if (k['e']) { t.y += spd; }
      if (k['q']) { t.y -= spd; }

      updateCamera();
      keyLoopRef.current = requestAnimationFrame(keyLoop);
    };
    keyLoopRef.current = requestAnimationFrame(keyLoop);

    // Animate loop
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      if (playingRef.current) {
        const t = clockRef.current.getElapsedTime();
        animRef.current.forEach(obj => {
          const { mesh, keyframes, loop, trailPoints } = obj;
          if (!keyframes || keyframes.length < 2) return;
          const dur = keyframes[keyframes.length - 1].t;
          if (dur <= 0) return;
          const ct = loop ? t % dur : Math.min(t, dur);
          let i = 0;
          while (i < keyframes.length - 2 && keyframes[i + 1].t <= ct) i++;
          const k0 = keyframes[i], k1 = keyframes[Math.min(i + 1, keyframes.length - 1)];
          const a = k1.t === k0.t ? 0 : (ct - k0.t) / (k1.t - k0.t);
          const nx = k0.x + (k1.x - k0.x) * a;
          const ny = k0.y + (k1.y - k0.y) * a;
          const nz = (k0.z || 0) + ((k1.z || 0) - (k0.z || 0)) * a;
          mesh.position.set(nx, ny, nz);
          if (obj.isRotating) mesh.rotation.y = nz;
          if (trailPoints) {
            trailPoints.push(new THREE.Vector3(nx, ny, nz));
            if (trailPoints.length > 500) trailPoints.shift();
            if (obj.trailLine) { sceneRef.current.remove(obj.trailLine); obj.trailLine.geometry.dispose(); }
            if (trailPoints.length > 1) {
              const tl = new THREE.Line(
                new THREE.BufferGeometry().setFromPoints(trailPoints),
                new THREE.LineBasicMaterial({ color: '#f59e0b', transparent: true, opacity: 0.55 })
              );
              obj.trailLine = tl;
              sceneRef.current.add(tl);
            }
          }
        });
      }
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

  // ── REBUILD SCENE ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!sceneRef.current) return;
    const scene = sceneRef.current;

    // Full clear
    animRef.current.forEach(obj => {
      scene.remove(obj.mesh);
      if (obj.mesh.geometry) obj.mesh.geometry.dispose();
      if (obj.trailLine) { scene.remove(obj.trailLine); obj.trailLine.geometry.dispose(); }
    });
    animRef.current = [];
    scene.children.filter(c => c.userData.isSim).forEach(c => {
      scene.remove(c);
      if (c.geometry) c.geometry.dispose();
    });
    labelDivs.current.forEach(d => { if (d.isConnected) d.remove(); });
    labelDivs.current = [];

    if (!simData) return;
    clockRef.current = new THREE.Clock();

    // Auto-position camera for optics (top-down 2D view)
    if (isOptics) {
      spherical.current = { theta: 0, phi: 0.01, radius: 18 };
      target.current.set(0, 0, 0);
      updateCamera();
    }

    const { objects = [], static_objects = [], vectors = [], lines = [], scene_labels = [] } = simData;

    static_objects.forEach(obj => {
      const m = buildMesh(obj);
      if (m) { m.userData.isSim = true; scene.add(m); }
    });

    objects.forEach(obj => {
      const m = buildMesh(obj);
      if (!m) return;
      const entry = {
        mesh: m,
        keyframes: obj.keyframes || [],
        loop: obj.loop !== false,
        trailPoints: obj.trail ? [] : null,
        trailLine: null,
        isRotating: obj.shape === 'disk_3d',
      };
      if (entry.keyframes.length > 0) {
        m.position.set(entry.keyframes[0].x || 0, entry.keyframes[0].y || 0, entry.keyframes[0].z || 0);
      }
      if (obj.label) m.add(makeSprite(obj.label, obj.color || '#fff'));
      scene.add(m);
      animRef.current.push(entry);
    });

    vectors.forEach(v => {
      if (!v?.origin || !v?.direction) return;
      const dir = new THREE.Vector3(...v.direction);
      const len = dir.length();
      if (len < 0.001) return;
      dir.normalize();
      const arrow = new THREE.ArrowHelper(
        dir, new THREE.Vector3(...v.origin),
        Math.max(0.3, Math.min(len, 8)),
        v.color || '#f59e0b',
        Math.min(0.35, len * 0.25), 0.14,
      );
      arrow.userData.isSim = true;
      scene.add(arrow);
      if (v.label) addHTMLLabel(v.label, new THREE.Vector3(...v.origin).add(dir.clone().multiplyScalar(len + 0.3)), v.color || '#f59e0b');
    });

    lines.forEach(lineData => {
      if (!lineData?.points || lineData.points.length < 2) return;
      const pts = lineData.points.map(p => new THREE.Vector3(p[0], p[1], p[2] || 0));
      const mat = new THREE.LineBasicMaterial({
        color: lineData.color || '#ffffff',
        transparent: true,
        opacity: lineData.dashed ? 0.3 : 0.92,
      });
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), mat);
      line.userData.isSim = true;
      scene.add(line);
      // Arrowhead on solid lines
      if (!lineData.dashed && pts.length >= 2) {
        const last = pts[pts.length - 1];
        const prev = pts[pts.length - 2];
        const dir  = last.clone().sub(prev);
        if (dir.length() > 0.01) {
          const arrow = new THREE.ArrowHelper(
            dir.normalize(), last, 0.001,
            lineData.color || '#ffffff', 0.45, 0.2,
          );
          arrow.userData.isSim = true;
          scene.add(arrow);
        }
      }
      if (lineData.label) {
        const mid = pts[Math.floor(pts.length / 2)].clone().add(new THREE.Vector3(0, 0.3, 0));
        addHTMLLabel(lineData.label, mid, lineData.color || '#aaa');
      }
    });

    scene_labels.forEach(lb => {
      if (!lb?.text?.trim()) return;
      addHTMLLabel(lb.text, new THREE.Vector3(lb.x || 0, lb.y || 0, lb.z || 0), lb.color || '#aaa');
    });

  }, [simData, isOptics]);

  function addHTMLLabel(text, position3D, color) {
    const mount = mountRef.current;
    if (!mount) return;
    const div = document.createElement('div');
    div.style.cssText = `
      position:absolute;pointer-events:none;font-size:11px;font-weight:700;
      font-family:'Inter',monospace;color:${color};
      background:rgba(5,5,15,0.82);padding:2px 7px;border-radius:4px;
      border:1px solid ${color}55;white-space:nowrap;
      transform:translate(-50%,-50%);z-index:10;
    `;
    div.textContent = text;
    mount.appendChild(div);
    div._pos = position3D.clone();
    labelDivs.current.push(div);
    const tick = () => {
      if (!div.isConnected || !cameraRef.current || !rendererRef.current) return;
      const canvas = rendererRef.current.domElement;
      const rect   = canvas.getBoundingClientRect();
      const v = div._pos.clone().project(cameraRef.current);
      div.style.left = ((v.x + 1) / 2 * rect.width)  + 'px';
      div.style.top  = ((1 - v.y) / 2 * rect.height) + 'px';
      div.style.display = v.z < 1 ? 'block' : 'none';
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

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
    <div ref={mountRef} style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden' }}>
      {loading && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          background: 'rgba(5,5,15,0.9)', zIndex: 20, gap: '14px',
        }}>
          <div style={{ fontSize: '38px', animation: 'spin 0.7s linear infinite' }}>⚡</div>
          <div style={{ color: '#f59e0b', fontSize: '15px', fontWeight: 700 }}>Solving physics problem...</div>
          <div style={{ color: '#444', fontSize: '12px' }}>LLM extraction → physics solver → 3D render</div>
          <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
        </div>
      )}
      {!simData && !loading && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          pointerEvents: 'none', gap: '10px',
        }}>
          <div style={{ fontSize: '52px', opacity: 0.15 }}>⚡</div>
          <div style={{ color: '#222', fontSize: '14px' }}>Select a chapter and describe a problem</div>
        </div>
      )}
      {/* Controls hint */}
      {simData && !loading && (
        <div style={{
          position: 'absolute', bottom: '14px', right: '14px',
          background: 'rgba(5,5,15,0.75)', border: '1px solid #1e1e2e',
          borderRadius: '8px', padding: '8px 12px',
          color: '#444', fontSize: '10px', lineHeight: '1.8',
          pointerEvents: 'none',
        }}>
          <div style={{ color: '#666', fontWeight: 700, marginBottom: '4px' }}>CAMERA</div>
          <div>🖱 Drag — orbit</div>
          <div>⚲ Scroll — zoom</div>
          <div><kbd style={kbdStyle}>W</kbd><kbd style={kbdStyle}>S</kbd> — forward/back</div>
          <div><kbd style={kbdStyle}>A</kbd><kbd style={kbdStyle}>D</kbd> — strafe</div>
          <div><kbd style={kbdStyle}>Q</kbd><kbd style={kbdStyle}>E</kbd> — down/up</div>
          <div><kbd style={kbdStyle}>R</kbd> — reset view</div>
        </div>
      )}
    </div>
  );
}

const kbdStyle = {
  background: '#1a1a2a', border: '1px solid #2a2a3a',
  borderRadius: '3px', padding: '0 4px', margin: '0 2px',
  fontSize: '9px', color: '#888',
};

// ── MESH BUILDER ─────────────────────────────────────────────────────────────

function buildMesh(obj) {
  const s = obj.size || 0.5;
  let geometry, material;

  switch (obj.shape) {
    case 'sphere':
      geometry = new THREE.SphereGeometry(s, 24, 24);
      break;
    case 'box':
      geometry = new THREE.BoxGeometry(s, s * (obj.height_ratio || 1), s);
      break;
    case 'cylinder':
      geometry = new THREE.CylinderGeometry(s * 0.25, s * 0.25, s * 3, 16);
      break;
    case 'disk_3d':
      geometry = new THREE.CylinderGeometry(obj.radius || s, obj.radius || s, 0.12, 32);
      break;
    case 'plane':
      geometry = new THREE.PlaneGeometry(obj.width || 20, obj.depth || 20);
      break;
    case 'custom_incline': {
      const ang = (obj.angle_deg || 30) * Math.PI / 180;
      const len = obj.length || 8;
      const shape = new THREE.Shape([
        new THREE.Vector2(0, 0),
        new THREE.Vector2(len * Math.cos(ang), len * Math.sin(ang)),
        new THREE.Vector2(len * Math.cos(ang), 0),
      ]);
      geometry = new THREE.ShapeGeometry(shape);
      material = new THREE.MeshPhongMaterial({ color: obj.color || '#2a2a3a', side: THREE.DoubleSide });
      const m = new THREE.Mesh(geometry, material);
      if (obj.position) m.position.set(...obj.position);
      return m;
    }
    default:
      geometry = new THREE.SphereGeometry(s, 12, 12);
  }

  material = new THREE.MeshPhongMaterial({
    color: obj.color || '#6366f1',
    shininess: 80,
    transparent: obj.shape === 'plane',
    opacity: obj.shape === 'plane' ? 0.7 : 1.0,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geometry, material);
  if (obj.position) mesh.position.set(...obj.position);
  if (obj.rotation) mesh.rotation.set(...obj.rotation);
  mesh.castShadow = true;
  return mesh;
}

function makeSprite(text, color = '#ffffff') {
  const canvas = document.createElement('canvas');
  canvas.width = 320; canvas.height = 72;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, 320, 72);
  ctx.fillStyle = 'rgba(0,0,0,0.72)';
  ctx.roundRect(2, 2, 316, 68, 10); ctx.fill();
  ctx.fillStyle = color;
  ctx.font = 'bold 26px Inter,Arial,sans-serif';
  ctx.fillText(text, 10, 48);
  const tex = new THREE.CanvasTexture(canvas);
  const sp  = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
  sp.scale.set(3.6, 0.9, 1);
  sp.position.set(0, 1.4, 0);
  return sp;
}

function addAxes(scene) {
  [[[1,0,0],'#ef444466'],[[0,1,0],'#22c55e66'],[[0,0,1],'#3b82f666']].forEach(([d, c]) => {
    scene.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(...d).multiplyScalar(8)]),
      new THREE.LineBasicMaterial({ color: c, transparent: true, opacity: 0.25 })
    ));
  });
}
