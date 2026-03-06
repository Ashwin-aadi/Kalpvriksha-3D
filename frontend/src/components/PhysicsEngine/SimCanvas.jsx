import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function SimCanvas({ simData, playing, loading }) {
  const mountRef    = useRef(null);
  const sceneRef    = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef   = useRef(null);
  const frameRef    = useRef(null);
  const clockRef    = useRef(new THREE.Clock());
  const animRef     = useRef([]);   // [{ mesh, keyframes, loop, trailMeshes }]
  const playingRef  = useRef(false);
  const spherical   = useRef({ theta: Math.PI / 4, phi: Math.PI / 3, radius: 20 });
  const isDragging  = useRef(false);
  const prevMouse   = useRef({ x: 0, y: 0 });

  playingRef.current = playing;

  // ── INIT SCENE ────────────────────────────────────────────────────────────
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#0a0a0f');
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(60, mount.clientWidth / mount.clientHeight, 0.1, 1000);
    cameraRef.current = camera;
    updateCamera();

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Permanent scene elements
    scene.add(new THREE.GridHelper(40, 40, '#1a1a2a', '#111118'));
    addAxes(scene);
    scene.add(new THREE.AmbientLight('#ffffff', 0.5));
    const sun = new THREE.DirectionalLight('#ffffff', 1);
    sun.position.set(10, 20, 10);
    scene.add(sun);

    // Mouse controls
    const onDown  = e => { isDragging.current = true; prevMouse.current = { x: e.clientX, y: e.clientY }; };
    const onUp    = () => { isDragging.current = false; };
    const onMove  = e => {
      if (!isDragging.current) return;
      spherical.current.theta -= (e.clientX - prevMouse.current.x) * 0.01;
      spherical.current.phi    = Math.max(0.1, Math.min(Math.PI - 0.1,
        spherical.current.phi - (e.clientY - prevMouse.current.y) * 0.01));
      prevMouse.current = { x: e.clientX, y: e.clientY };
      updateCamera();
    };
    const onWheel = e => {
      spherical.current.radius = Math.max(3, Math.min(80, spherical.current.radius + e.deltaY * 0.05));
      updateCamera();
    };
    mount.addEventListener('mousedown', onDown);
    mount.addEventListener('mouseup',   onUp);
    mount.addEventListener('mousemove', onMove);
    mount.addEventListener('wheel',     onWheel);

    // Animate loop
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      if (playingRef.current) {
        const t = clockRef.current.getElapsedTime();
        animRef.current.forEach(obj => {
          const { mesh, keyframes, loop, trailPoints } = obj;
          if (!keyframes || keyframes.length < 2) return;
          const duration = keyframes[keyframes.length - 1].t;
          const ct = loop ? t % duration : Math.min(t, duration);

          // Find surrounding keyframes
          let i = 0;
          while (i < keyframes.length - 2 && keyframes[i + 1].t <= ct) i++;
          const k0 = keyframes[i];
          const k1 = keyframes[Math.min(i + 1, keyframes.length - 1)];
          const alpha = k1.t === k0.t ? 0 : (ct - k0.t) / (k1.t - k0.t);

          const nx = k0.x + (k1.x - k0.x) * alpha;
          const ny = k0.y + (k1.y - k0.y) * alpha;
          const nz = (k0.z || 0) + ((k1.z || 0) - (k0.z || 0)) * alpha;
          mesh.position.set(nx, ny, nz);

          // Trail
          if (trailPoints) {
            trailPoints.push(new THREE.Vector3(nx, ny, nz));
            if (trailPoints.length > 300) trailPoints.shift();
            // Remove old trail line
            if (obj.trailLine) {
              sceneRef.current.remove(obj.trailLine);
              obj.trailLine.geometry.dispose();
              obj.trailLine = null;
            }
            if (trailPoints.length > 1) {
              const geo  = new THREE.BufferGeometry().setFromPoints(trailPoints);
              const line = new THREE.Line(geo, new THREE.LineBasicMaterial({
                color: '#f59e0b', transparent: true, opacity: 0.6,
              }));
              obj.trailLine = line;
              sceneRef.current.add(line);
            }
          }
        });
      }
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      if (!mount) return;
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(frameRef.current);
      mount.removeEventListener('mousedown', onDown);
      mount.removeEventListener('mouseup',   onUp);
      mount.removeEventListener('mousemove', onMove);
      mount.removeEventListener('wheel',     onWheel);
      window.removeEventListener('resize',   onResize);
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, []);

  // ── REBUILD SCENE WHEN simData CHANGES ────────────────────────────────────
  useEffect(() => {
    if (!sceneRef.current) return;
    const scene = sceneRef.current;

    // ── FULL CLEAR of previous sim objects ──
    animRef.current.forEach(obj => {
      scene.remove(obj.mesh);
      obj.mesh.geometry.dispose();
      obj.mesh.material.dispose();
      if (obj.trailLine) {
        scene.remove(obj.trailLine);
        obj.trailLine.geometry.dispose();
      }
    });
    animRef.current = [];

    // Remove all tagged sim objects (static, vectors)
    const toRemove = scene.children.filter(c => c.userData.isSim);
    toRemove.forEach(c => {
      scene.remove(c);
      if (c.geometry) c.geometry.dispose();
      if (c.material) c.material.dispose();
    });

    if (!simData) return;

    // Reset clock so animation restarts from 0
    clockRef.current = new THREE.Clock();

    const { objects = [], static_objects = [], vectors = [] } = simData;

    // Static objects
    static_objects.forEach(obj => {
      const mesh = buildMesh(obj);
      if (mesh) { mesh.userData.isSim = true; scene.add(mesh); }
    });

    // Animated objects
    objects.forEach(obj => {
      const mesh = buildMesh(obj);
      if (!mesh) return;
      mesh.userData.isSim = false; // managed separately

      const entry = {
        mesh,
        keyframes: obj.keyframes || [],
        loop: obj.loop !== false,
        trailPoints: obj.trail ? [] : null,
        trailLine: null,
      };

      // Set initial position
      if (entry.keyframes.length > 0) {
        const k0 = entry.keyframes[0];
        mesh.position.set(k0.x, k0.y, k0.z || 0);
      }

      // Label sprite
      if (obj.label) {
        mesh.add(makeLabel(obj.label));
      }

      scene.add(mesh);
      animRef.current.push(entry);
    });

    // Vectors / arrows
    vectors.forEach(({ origin, direction, color }) => {
      if (!origin || !direction) return;
      const dir = new THREE.Vector3(...direction);
      const len = dir.length();
      if (len < 0.001) return;
      dir.normalize();
      const arrow = new THREE.ArrowHelper(
        dir,
        new THREE.Vector3(...origin),
        Math.max(0.5, len),
        color || '#f59e0b',
        Math.min(0.3, len * 0.2),
        0.12,
      );
      arrow.userData.isSim = true;
      scene.add(arrow);
    });

  }, [simData]);

  function updateCamera() {
    const { theta, phi, radius } = spherical.current;
    cameraRef.current.position.set(
      radius * Math.sin(phi) * Math.cos(theta),
      radius * Math.cos(phi),
      radius * Math.sin(phi) * Math.sin(theta),
    );
    cameraRef.current.lookAt(0, 0, 0);
  }

  return (
    <div ref={mountRef} style={{ width: '100%', height: '100%', position: 'relative' }}>
      {loading && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          background: 'rgba(10,10,15,0.85)', zIndex: 10,
          fontSize: '16px', color: '#f59e0b', gap: '12px',
        }}>
          <div style={{ fontSize: '36px', animation: 'spin 1s linear infinite' }}>⚡</div>
          Solving physics problem...
        </div>
      )}
      {!simData && !loading && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          color: '#2a2a3a', pointerEvents: 'none',
        }}>
          <div style={{ fontSize: '56px', marginBottom: '16px' }}>⚡</div>
          <div style={{ fontSize: '16px', color: '#333' }}>Describe a physics problem and click Solve</div>
          <div style={{ fontSize: '12px', marginTop: '8px', color: '#222' }}>
            drag to rotate · scroll to zoom
          </div>
        </div>
      )}
    </div>
  );
}

// ── HELPERS ──────────────────────────────────────────────────────────────────

function buildMesh(obj) {
  const s = obj.size || 0.5;
  let geometry;
  switch (obj.shape) {
    case 'sphere':   geometry = new THREE.SphereGeometry(s, 20, 20); break;
    case 'box':      geometry = new THREE.BoxGeometry(s, s * (obj.height_ratio || 1), s); break;
    case 'cylinder': geometry = new THREE.CylinderGeometry(s * 0.25, s * 0.25, s * 3, 12); break;
    case 'cone':     geometry = new THREE.ConeGeometry(s, s * 2, 12); break;
    case 'plane': {
      geometry = new THREE.PlaneGeometry(obj.width || 20, obj.depth || 20);
      break;
    }
    default: geometry = new THREE.SphereGeometry(s, 12, 12);
  }

  const material = new THREE.MeshPhongMaterial({ color: obj.color || '#6366f1', shininess: 60 });
  const mesh = new THREE.Mesh(geometry, material);

  if (obj.position) mesh.position.set(...obj.position);
  if (obj.rotation) mesh.rotation.set(...obj.rotation);

  return mesh;
}

function makeLabel(text) {
  const canvas = document.createElement('canvas');
  canvas.width = 256; canvas.height = 64;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, 256, 64);
  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  ctx.roundRect(2, 2, 252, 60, 8);
  ctx.fill();
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 26px Inter, Arial, sans-serif';
  ctx.fillText(text, 10, 44);
  const tex    = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
  sprite.scale.set(3.2, 0.8, 1);
  sprite.position.set(0, 1.2, 0);
  return sprite;
}

function addAxes(scene) {
  [
    { dir: [1, 0, 0], color: '#ef4444' },
    { dir: [0, 1, 0], color: '#22c55e' },
    { dir: [0, 0, 1], color: '#3b82f6' },
  ].forEach(({ dir, color }) => {
    const pts = [new THREE.Vector3(0,0,0), new THREE.Vector3(...dir).multiplyScalar(10)];
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.35 }),
    );
    scene.add(line);
  });
}
