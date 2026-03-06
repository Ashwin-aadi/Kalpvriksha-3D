import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function SimCanvas({ simData, playing, loading }) {
  const mountRef   = useRef(null);
  const sceneRef   = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef  = useRef(null);
  const frameRef   = useRef(null);
  const clockRef   = useRef(new THREE.Clock());
  const objectsRef = useRef([]);    // animated objects [{mesh, keyframes}]
  const playingRef = useRef(false);
  const spherical  = useRef({ theta: Math.PI / 4, phi: Math.PI / 3, radius: 20 });
  const isDragging = useRef(false);
  const prevMouse  = useRef({ x: 0, y: 0 });

  playingRef.current = playing;

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
    renderer.shadowMap.enabled = true;
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Ground grid
    const grid = new THREE.GridHelper(40, 40, '#1a1a2a', '#111118');
    scene.add(grid);

    // Axes
    addAxes(scene);

    // Lighting
    scene.add(new THREE.AmbientLight('#ffffff', 0.5));
    const sun = new THREE.DirectionalLight('#ffffff', 1);
    sun.position.set(10, 20, 10);
    sun.castShadow = true;
    scene.add(sun);

    // Mouse controls
    const onDown = e => { isDragging.current = true; prevMouse.current = { x: e.clientX, y: e.clientY }; };
    const onUp   = () => { isDragging.current = false; };
    const onMove = e => {
      if (!isDragging.current) return;
      spherical.current.theta -= (e.clientX - prevMouse.current.x) * 0.01;
      spherical.current.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.current.phi - (e.clientY - prevMouse.current.y) * 0.01));
      prevMouse.current = { x: e.clientX, y: e.clientY };
      updateCamera();
    };
    const onWheel = e => {
      spherical.current.radius = Math.max(3, Math.min(80, spherical.current.radius + e.deltaY * 0.05));
      updateCamera();
    };

    mount.addEventListener('mousedown', onDown);
    mount.addEventListener('mouseup', onUp);
    mount.addEventListener('mousemove', onMove);
    mount.addEventListener('wheel', onWheel);

    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      if (playingRef.current) {
        const t = clockRef.current.getElapsedTime();
        objectsRef.current.forEach(({ mesh, keyframes, loop }) => {
          if (!keyframes || keyframes.length < 2) return;
          const duration = keyframes[keyframes.length - 1].t;
          const ct = loop ? t % duration : Math.min(t, duration);
          // Interpolate position
          let i = 0;
          while (i < keyframes.length - 1 && keyframes[i + 1].t < ct) i++;
          const k0 = keyframes[i], k1 = keyframes[Math.min(i + 1, keyframes.length - 1)];
          const alpha = k1.t === k0.t ? 0 : (ct - k0.t) / (k1.t - k0.t);
          mesh.position.set(
            k0.x + (k1.x - k0.x) * alpha,
            k0.y + (k1.y - k0.y) * alpha,
            k0.z + (k1.z - k0.z) * alpha,
          );
          if (mesh.userData.trailPoints) {
            mesh.userData.trailPoints.push(mesh.position.clone());
            if (mesh.userData.trailPoints.length > 200) mesh.userData.trailPoints.shift();
            if (mesh.userData.trailLine) {
              sceneRef.current.remove(mesh.userData.trailLine);
            }
            if (mesh.userData.trailPoints.length > 1) {
              const tgeo = new THREE.BufferGeometry().setFromPoints(mesh.userData.trailPoints);
              const tline = new THREE.Line(tgeo, new THREE.LineBasicMaterial({ color: '#f59e0b', transparent: true, opacity: 0.5 }));
              mesh.userData.trailLine = tline;
              sceneRef.current.add(tline);
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
      mount.removeEventListener('mousedown', onDown);
      mount.removeEventListener('mouseup', onUp);
      mount.removeEventListener('mousemove', onMove);
      mount.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', onResize);
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, []);

  // Build scene from simData
  useEffect(() => {
    if (!sceneRef.current || !simData) return;
    const scene = sceneRef.current;

    // Clear animated objects
    objectsRef.current.forEach(({ mesh }) => scene.remove(mesh));
    objectsRef.current = [];
    scene.children.filter(c => c.userData.isSim).forEach(c => scene.remove(c));
    clockRef.current = new THREE.Clock();

    const { objects, static_objects, vectors } = simData;

    // Static objects (ground, walls, etc.)
    if (static_objects) {
      static_objects.forEach(obj => {
        const mesh = buildMesh(obj);
        if (mesh) { mesh.userData.isSim = true; scene.add(mesh); }
      });
    }

    // Animated objects
    if (objects) {
      objects.forEach(obj => {
        const mesh = buildMesh(obj);
        if (!mesh) return;
        if (obj.trail) { mesh.userData.trailPoints = []; }
        mesh.userData.isSim = true;
        scene.add(mesh);
        objectsRef.current.push({ mesh, keyframes: obj.keyframes, loop: obj.loop || false });

        // Label
        if (obj.label) {
          // Simple sprite label using canvas texture
          const canvas = document.createElement('canvas');
          canvas.width = 256; canvas.height = 64;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = 'rgba(0,0,0,0)';
          ctx.fillRect(0, 0, 256, 64);
          ctx.fillStyle = '#fff';
          ctx.font = 'bold 28px Inter, sans-serif';
          ctx.fillText(obj.label, 8, 44);
          const tex = new THREE.CanvasTexture(canvas);
          const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
          sprite.scale.set(3, 0.75, 1);
          sprite.position.set(0, obj.size ? obj.size * 1.5 : 1.5, 0);
          mesh.add(sprite);
        }
      });
    }

    // Static vectors/arrows
    if (vectors) {
      vectors.forEach(({ origin, direction, color, label }) => {
        const dir = new THREE.Vector3(...direction).normalize();
        const len = new THREE.Vector3(...direction).length();
        const arrow = new THREE.ArrowHelper(dir, new THREE.Vector3(...origin), Math.max(0.5, len), color || '#f59e0b');
        arrow.userData.isSim = true;
        scene.add(arrow);
      });
    }
  }, [simData]);

  function buildMesh(obj) {
    let geometry;
    const s = obj.size || 0.5;
    switch (obj.shape) {
      case 'sphere':   geometry = new THREE.SphereGeometry(s, 16, 16); break;
      case 'box':      geometry = new THREE.BoxGeometry(s, s * (obj.height_ratio || 1), s); break;
      case 'cylinder': geometry = new THREE.CylinderGeometry(s * 0.3, s, s * 2, 12); break;
      case 'cone':     geometry = new THREE.ConeGeometry(s, s * 2, 12); break;
      case 'plane':
        geometry = new THREE.PlaneGeometry(obj.width || 20, obj.depth || 20);
        break;
      default: geometry = new THREE.SphereGeometry(s, 12, 12);
    }
    const color = obj.color || '#6366f1';
    const material = new THREE.MeshPhongMaterial({ color, shininess: 80 });
    const mesh = new THREE.Mesh(geometry, material);
    if (obj.keyframes && obj.keyframes.length > 0) {
      mesh.position.set(obj.keyframes[0].x, obj.keyframes[0].y, obj.keyframes[0].z);
    } else if (obj.position) {
      mesh.position.set(...obj.position);
    }
    if (obj.rotation) mesh.rotation.set(...obj.rotation);
    return mesh;
  }

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
          position: 'absolute', inset: 0, display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          background: 'rgba(10,10,15,0.8)', zIndex: 10,
          fontSize: '16px', color: '#f59e0b', flexDirection: 'column', gap: '12px',
        }}>
          <div style={{ fontSize: '32px' }}>⚡</div>
          Solving physics problem...
        </div>
      )}
      {!simData && !loading && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          color: '#333', pointerEvents: 'none',
        }}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>⚡</div>
          <div style={{ fontSize: '16px' }}>Describe a physics problem and click Solve</div>
          <div style={{ fontSize: '12px', marginTop: '6px', color: '#222' }}>
            drag to rotate · scroll to zoom
          </div>
        </div>
      )}
    </div>
  );
}

function addAxes(scene) {
  [
    { dir: [1,0,0], color: '#ef4444' },
    { dir: [0,1,0], color: '#22c55e' },
    { dir: [0,0,1], color: '#3b82f6' },
  ].forEach(({ dir, color }) => {
    const pts = [new THREE.Vector3(0,0,0), new THREE.Vector3(...dir).multiplyScalar(10)];
    scene.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.4 })
    ));
  });
}
