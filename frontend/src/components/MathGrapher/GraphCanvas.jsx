import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function GraphCanvas({ plotData, loading }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const frameRef = useRef(null);
  const isDragging = useRef(false);
  const prevMouse = useRef({ x: 0, y: 0 });
  const spherical = useRef({ theta: Math.PI / 4, phi: Math.PI / 3, radius: 15 });

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // Scene setup
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

    // Axes
    addAxes(scene);

    // Grid
    const grid = new THREE.GridHelper(20, 20, '#1a1a2a', '#1a1a2a');
    scene.add(grid);

    // Lighting
    scene.add(new THREE.AmbientLight('#ffffff', 0.6));
    const dirLight = new THREE.DirectionalLight('#ffffff', 0.8);
    dirLight.position.set(10, 20, 10);
    scene.add(dirLight);

    // Mouse controls
    const onMouseDown = e => { isDragging.current = true; prevMouse.current = { x: e.clientX, y: e.clientY }; };
    const onMouseUp = () => { isDragging.current = false; };
    const onMouseMove = e => {
      if (!isDragging.current) return;
      const dx = e.clientX - prevMouse.current.x;
      const dy = e.clientY - prevMouse.current.y;
      spherical.current.theta -= dx * 0.01;
      spherical.current.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.current.phi - dy * 0.01));
      prevMouse.current = { x: e.clientX, y: e.clientY };
      updateCamera();
    };
    const onWheel = e => {
      spherical.current.radius = Math.max(3, Math.min(50, spherical.current.radius + e.deltaY * 0.02));
      updateCamera();
    };

    mount.addEventListener('mousedown', onMouseDown);
    mount.addEventListener('mouseup', onMouseUp);
    mount.addEventListener('mousemove', onMouseMove);
    mount.addEventListener('wheel', onWheel);

    // Animate
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    // Resize
    const onResize = () => {
      if (!mount) return;
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(frameRef.current);
      mount.removeEventListener('mousedown', onMouseDown);
      mount.removeEventListener('mouseup', onMouseUp);
      mount.removeEventListener('mousemove', onMouseMove);
      mount.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', onResize);
      mount.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, []);

  function updateCamera() {
    const { theta, phi, radius } = spherical.current;
    cameraRef.current.position.set(
      radius * Math.sin(phi) * Math.cos(theta),
      radius * Math.cos(phi),
      radius * Math.sin(phi) * Math.sin(theta),
    );
    cameraRef.current.lookAt(0, 0, 0);
  }

  // When plotData changes, rebuild mesh
  useEffect(() => {
    if (!sceneRef.current || !plotData) return;
    const scene = sceneRef.current;

    // Remove old plot objects
    const toRemove = scene.children.filter(c => c.userData.isPlot);
    toRemove.forEach(c => scene.remove(c));

    const { plot_type, points, triangles, color } = plotData;

    if (plot_type === 'surface' && points && triangles) {
      const geometry = new THREE.BufferGeometry();
      const verts = new Float32Array(points.flat());
      geometry.setAttribute('position', new THREE.BufferAttribute(verts, 3));
      geometry.setIndex(triangles.flat());
      geometry.computeVertexNormals();

      // Color by height
      const colors = new Float32Array(points.length * 3);
      const ys = points.map(p => p[1]);
      const minY = Math.min(...ys), maxY = Math.max(...ys);
      points.forEach((p, i) => {
        const t = maxY === minY ? 0.5 : (p[1] - minY) / (maxY - minY);
        const c = new THREE.Color().setHSL(0.66 - t * 0.66, 1, 0.5);
        colors[i * 3] = c.r; colors[i * 3 + 1] = c.g; colors[i * 3 + 2] = c.b;
      });
      geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

      const mesh = new THREE.Mesh(geometry, new THREE.MeshPhongMaterial({
        vertexColors: true, side: THREE.DoubleSide,
        shininess: 60, transparent: true, opacity: 0.85,
      }));
      mesh.userData.isPlot = true;
      scene.add(mesh);

      // Wireframe overlay
      const wire = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
        color: '#ffffff', wireframe: true, transparent: true, opacity: 0.08,
      }));
      wire.userData.isPlot = true;
      scene.add(wire);

    } else if (plot_type === 'curve' && points) {
      const pts = points.map(p => new THREE.Vector3(p[0], p[1], p[2] || 0));
      const geometry = new THREE.BufferGeometry().setFromPoints(pts);
      const line = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: '#10b981', linewidth: 2 }));
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

    // Auto-fit camera
    if (points && points.length > 0) {
      const flat = points.flat ? points.flat() : points.flatMap(p => p.origin || p);
      const maxVal = Math.max(...flat.map(Math.abs).filter(v => isFinite(v)));
      if (maxVal > 0) {
        spherical.current.radius = Math.min(50, Math.max(8, maxVal * 2.5));
        updateCamera();
      }
    }
  }, [plotData]);

  return (
    <div ref={mountRef} style={{ width: '100%', height: '100%', position: 'relative' }}>
      {loading && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          background: 'rgba(10,10,15,0.7)', zIndex: 10,
          fontSize: '16px', color: '#10b981',
        }}>
          ⏳ Computing plot...
        </div>
      )}
      {!plotData && !loading && (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          color: '#333', pointerEvents: 'none',
        }}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>📐</div>
          <div style={{ fontSize: '16px' }}>Enter an equation and click Plot</div>
          <div style={{ fontSize: '12px', marginTop: '6px', color: '#222' }}>
            drag to rotate · scroll to zoom
          </div>
        </div>
      )}
    </div>
  );
}

function addAxes(scene) {
  const axes = [
    { dir: [1,0,0], color: '#ef4444', label: 'X' },
    { dir: [0,1,0], color: '#22c55e', label: 'Y' },
    { dir: [0,0,1], color: '#3b82f6', label: 'Z' },
  ];
  axes.forEach(({ dir, color }) => {
    const pts = [new THREE.Vector3(0,0,0), new THREE.Vector3(...dir).multiplyScalar(8)];
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    const line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color }));
    scene.add(line);
    // Negative axis (dashed look — just dimmer)
    const neg = [new THREE.Vector3(0,0,0), new THREE.Vector3(...dir).multiplyScalar(-4)];
    const negGeo = new THREE.BufferGeometry().setFromPoints(neg);
    const negLine = new THREE.Line(negGeo, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.2 }));
    scene.add(negLine);
  });
}
