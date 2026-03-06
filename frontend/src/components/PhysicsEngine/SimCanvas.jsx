import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export function SimCanvas({ simData, playing, loading }) {
  const mountRef   = useRef(null);
  const sceneRef   = useRef(null);
  const rendererRef= useRef(null);
  const cameraRef  = useRef(null);
  const frameRef   = useRef(null);
  const clockRef   = useRef(new THREE.Clock());
  const animRef    = useRef([]);
  const playingRef = useRef(false);
  const spherical  = useRef({ theta: Math.PI/4, phi: Math.PI/3, radius: 22 });
  const isDragging = useRef(false);
  const prevMouse  = useRef({ x:0, y:0 });
  const labelDivs  = useRef([]);

  playingRef.current = playing;

  // ── INIT ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#080810');
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(55, mount.clientWidth/mount.clientHeight, 0.01, 1000);
    cameraRef.current = camera;
    updateCamera();

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Base scene
    const grid = new THREE.GridHelper(40, 40, '#1a1a2a', '#0f0f1a');
    grid.material.opacity = 0.4; grid.material.transparent = true;
    scene.add(grid);
    addAxes(scene);
    scene.add(new THREE.AmbientLight('#ffffff', 0.6));
    const sun = new THREE.DirectionalLight('#ffffff', 1);
    sun.position.set(10,20,10); sun.castShadow=true; scene.add(sun);

    // Controls
    const onDown  = e => { isDragging.current=true; prevMouse.current={x:e.clientX,y:e.clientY}; };
    const onUp    = () => { isDragging.current=false; };
    const onMove  = e => {
      if (!isDragging.current) return;
      spherical.current.theta -= (e.clientX-prevMouse.current.x)*0.008;
      spherical.current.phi = Math.max(0.05, Math.min(Math.PI-0.05,
        spherical.current.phi-(e.clientY-prevMouse.current.y)*0.008));
      prevMouse.current = {x:e.clientX, y:e.clientY};
      updateCamera();
    };
    const onWheel = e => {
      spherical.current.radius = Math.max(2, Math.min(100, spherical.current.radius+e.deltaY*0.04));
      updateCamera();
    };
    mount.addEventListener('mousedown', onDown);
    mount.addEventListener('mouseup', onUp);
    mount.addEventListener('mousemove', onMove);
    mount.addEventListener('wheel', onWheel);

    // Animate
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      if (playingRef.current) {
        const t = clockRef.current.getElapsedTime();
        animRef.current.forEach(obj => {
          const { mesh, keyframes, loop, trailPoints } = obj;
          if (!keyframes || keyframes.length < 2) return;
          const dur = keyframes[keyframes.length-1].t;
          if (dur <= 0) return;
          const ct = loop ? t % dur : Math.min(t, dur);
          let i = 0;
          while (i < keyframes.length-2 && keyframes[i+1].t <= ct) i++;
          const k0=keyframes[i], k1=keyframes[Math.min(i+1,keyframes.length-1)];
          const a = k1.t===k0.t ? 0 : (ct-k0.t)/(k1.t-k0.t);
          const nx=k0.x+(k1.x-k0.x)*a, ny=k0.y+(k1.y-k0.y)*a, nz=(k0.z||0)+((k1.z||0)-(k0.z||0))*a;
          mesh.position.set(nx, ny, nz);
          if (obj.shape === 'disk_3d') {
            mesh.rotation.y = nz; // use z keyframe as rotation
          }
          if (trailPoints) {
            trailPoints.push(new THREE.Vector3(nx, ny, nz));
            if (trailPoints.length > 400) trailPoints.shift();
            if (obj.trailLine) { sceneRef.current.remove(obj.trailLine); obj.trailLine.geometry.dispose(); }
            if (trailPoints.length > 1) {
              const tl = new THREE.Line(
                new THREE.BufferGeometry().setFromPoints(trailPoints),
                new THREE.LineBasicMaterial({ color: '#f59e0b', transparent: true, opacity: 0.5 })
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
      camera.aspect = mount.clientWidth/mount.clientHeight;
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

  // ── REBUILD on simData change ─────────────────────────────────────────────
  useEffect(() => {
    if (!sceneRef.current) return;
    const scene = sceneRef.current;

    // Full clear
    animRef.current.forEach(obj => {
      scene.remove(obj.mesh);
      if (obj.mesh.geometry) obj.mesh.geometry.dispose();
      if (obj.mesh.material) obj.mesh.material.dispose();
      if (obj.trailLine) { scene.remove(obj.trailLine); obj.trailLine.geometry.dispose(); }
    });
    animRef.current = [];
    scene.children.filter(c => c.userData.isSim).forEach(c => {
      scene.remove(c);
      if (c.geometry) c.geometry.dispose();
    });
    // Clear HTML labels
    labelDivs.current.forEach(d => d.remove());
    labelDivs.current = [];

    if (!simData) return;
    clockRef.current = new THREE.Clock();

    const { objects=[], static_objects=[], vectors=[], lines=[], scene_labels=[] } = simData;

    // Static objects
    static_objects.forEach(obj => {
      const m = buildMesh(obj);
      if (m) { m.userData.isSim=true; scene.add(m); }
    });

    // Animated objects
    objects.forEach(obj => {
      const m = buildMesh(obj);
      if (!m) return;
      const entry = { mesh:m, keyframes:obj.keyframes||[], loop:obj.loop!==false,
                      trailPoints:obj.trail ? [] : null, trailLine:null, shape:obj.shape };
      if (entry.keyframes.length>0) m.position.set(entry.keyframes[0].x||0, entry.keyframes[0].y||0, entry.keyframes[0].z||0);
      if (obj.label) m.add(makeSprite(obj.label, obj.color||'#fff'));
      scene.add(m);
      animRef.current.push(entry);
    });

    // Vectors / arrows
    vectors.forEach(v => {
      if (!v?.origin || !v?.direction) return;
      const dir = new THREE.Vector3(...v.direction);
      const len = dir.length();
      if (len < 0.001) return;
      dir.normalize();
      const arrow = new THREE.ArrowHelper(
        dir, new THREE.Vector3(...v.origin),
        Math.max(0.3, Math.min(len, 8)),
        v.color||'#f59e0b', Math.min(0.35, len*0.25), 0.14
      );
      arrow.userData.isSim=true;
      scene.add(arrow);
      if (v.label) {
        const tip = new THREE.Vector3(...v.origin).add(dir.clone().multiplyScalar(len+0.3));
        addHTMLLabel(v.label, tip, v.color||'#f59e0b');
      }
    });

    // Lines (ray tracing, graphs, etc.)
    lines.forEach(lineData => {
      if (!lineData?.points || lineData.points.length < 2) return;
      const pts = lineData.points.map(p => new THREE.Vector3(p[0],p[1],p[2]||0));
      const material = new THREE.LineBasicMaterial({
        color: lineData.color||'#ffffff', transparent:true,
        opacity: lineData.dashed ? 0.35 : 0.9,
      });
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const line = new THREE.Line(geo, material);
      line.userData.isSim=true;
      scene.add(line);
      // Arrow head on non-dashed lines
      if (!lineData.dashed && pts.length >= 2) {
        const last = pts[pts.length-1];
        const prev = pts[pts.length-2];
        const dir  = last.clone().sub(prev).normalize();
        if (dir.length() > 0.001) {
          const arr = new THREE.ArrowHelper(dir, last, 0.001,
            lineData.color||'#ffffff', 0.4, 0.18);
          arr.userData.isSim=true;
          scene.add(arr);
        }
      }
      if (lineData.label) {
        const mid = pts[Math.floor(pts.length/2)];
        addHTMLLabel(lineData.label, mid, lineData.color||'#aaa');
      }
    });

    // 3D scene labels
    scene_labels.forEach(lb => {
      if (!lb?.text) return;
      const pos = new THREE.Vector3(lb.x||0, lb.y||0, lb.z||0);
      addHTMLLabel(lb.text, pos, lb.color||'#aaa');
    });

  }, [simData]);

  function addHTMLLabel(text, position3D, color) {
    const mount = mountRef.current;
    if (!mount || !cameraRef.current || !rendererRef.current) return;
    // We store {text, pos, color, el} and project each frame
    const div = document.createElement('div');
    div.style.cssText = `position:absolute;pointer-events:none;font-size:11px;font-weight:600;
      font-family:'Inter',sans-serif;color:${color};
      background:rgba(8,8,16,0.75);padding:2px 6px;border-radius:4px;
      border:1px solid ${color}44;white-space:nowrap;transform:translate(-50%,-50%);`;
    div.textContent = text;
    mount.appendChild(div);
    div._pos3d = position3D.clone();
    div._color = color;
    labelDivs.current.push(div);

    // Update label position every frame
    const updatePos = () => {
      if (!div.isConnected) return;
      if (!cameraRef.current || !rendererRef.current) { requestAnimationFrame(updatePos); return; }
      const canvas = rendererRef.current.domElement;
      const rect   = canvas.getBoundingClientRect();
      const vec    = div._pos3d.clone().project(cameraRef.current);
      const sx = (vec.x+1)/2 * rect.width;
      const sy = (1-vec.y)/2 * rect.height;
      div.style.left = sx+'px';
      div.style.top  = sy+'px';
      div.style.display = (vec.z < 1) ? 'block' : 'none';
      requestAnimationFrame(updatePos);
    };
    requestAnimationFrame(updatePos);
  }

  function updateCamera() {
    const { theta, phi, radius } = spherical.current;
    cameraRef.current.position.set(
      radius*Math.sin(phi)*Math.cos(theta),
      radius*Math.cos(phi),
      radius*Math.sin(phi)*Math.sin(theta)
    );
    cameraRef.current.lookAt(0,0,0);
  }

  return (
    <div ref={mountRef} style={{ width:'100%', height:'100%', position:'relative', overflow:'hidden' }}>
      {loading && (
        <div style={{
          position:'absolute',inset:0,display:'flex',flexDirection:'column',
          alignItems:'center',justifyContent:'center',
          background:'rgba(8,8,16,0.88)',zIndex:20,gap:'14px',
        }}>
          <div style={{ fontSize:'40px', animation:'spin 0.8s linear infinite' }}>⚡</div>
          <div style={{ color:'#f59e0b', fontSize:'15px', fontWeight:600 }}>Solving physics problem...</div>
          <div style={{ color:'#555', fontSize:'12px' }}>Extracting parameters via LLM · Computing · Rendering</div>
          <style>{`@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}`}</style>
        </div>
      )}
      {!simData && !loading && (
        <div style={{
          position:'absolute',inset:0,display:'flex',flexDirection:'column',
          alignItems:'center',justifyContent:'center',pointerEvents:'none',gap:'12px',
        }}>
          <div style={{ fontSize:'52px' }}>⚡</div>
          <div style={{ color:'#2a2a3a', fontSize:'16px' }}>Select a chapter · Describe the problem · Click Solve</div>
          <div style={{ color:'#1a1a2a', fontSize:'12px' }}>drag to rotate · scroll to zoom</div>
        </div>
      )}
      {simData && (
        <div style={{
          position:'absolute',top:'12px',right:'12px',
          background:'rgba(8,8,16,0.7)',border:'1px solid #1e1e2e',
          borderRadius:'8px',padding:'6px 12px',
          color:'#555',fontSize:'11px',pointerEvents:'none',
        }}>
          drag to rotate · scroll to zoom
        </div>
      )}
    </div>
  );
}

// ── MESH BUILDER ─────────────────────────────────────────────────────────────

function buildMesh(obj) {
  const s = obj.size || 0.5;
  let geometry;
  switch (obj.shape) {
    case 'sphere':   geometry = new THREE.SphereGeometry(s, 24, 24); break;
    case 'box':      geometry = new THREE.BoxGeometry(s, s*(obj.height_ratio||1), s); break;
    case 'cylinder': geometry = new THREE.CylinderGeometry(s*0.25, s*0.25, s*3, 16); break;
    case 'cone':     geometry = new THREE.ConeGeometry(s, s*2, 16); break;
    case 'disk_3d':  geometry = new THREE.CylinderGeometry(obj.radius||s, obj.radius||s, s*0.15, 32); break;
    case 'plane': {
      geometry = new THREE.PlaneGeometry(obj.width||20, obj.depth||20);
      break;
    }
    case 'custom_incline': {
      const ang = (obj.angle_deg||30) * Math.PI/180;
      const len = obj.length||8;
      const pts = [
        new THREE.Vector2(0, 0),
        new THREE.Vector2(len*Math.cos(ang), len*Math.sin(ang)),
        new THREE.Vector2(len*Math.cos(ang), 0),
      ];
      geometry = new THREE.ShapeGeometry(new THREE.Shape(pts));
      const m = new THREE.Mesh(geometry, new THREE.MeshPhongMaterial({
        color: obj.color||'#2a2a3a', side:THREE.DoubleSide, transparent:true, opacity:0.9
      }));
      if (obj.position) m.position.set(...obj.position);
      return m;
    }
    case 'lens_convex': {
      // Approximate lens with TorusGeometry slice
      geometry = new THREE.TorusGeometry(obj.height||2, 0.1, 8, 32, Math.PI*0.4);
      break;
    }
    case 'mirror_concave':
    case 'mirror_convex': {
      geometry = new THREE.TorusGeometry(obj.height||2, 0.05, 4, 32, Math.PI*0.5);
      break;
    }
    default: geometry = new THREE.SphereGeometry(s, 12, 12);
  }

  const material = new THREE.MeshPhongMaterial({
    color: obj.color||'#6366f1', shininess:80,
    transparent: ['lens_convex','lens_concave','mirror_concave','mirror_convex'].includes(obj.shape),
    opacity: ['lens_convex','lens_concave'].includes(obj.shape) ? 0.3 : 0.9,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geometry, material);
  if (obj.position) mesh.position.set(...obj.position);
  if (obj.rotation) mesh.rotation.set(...obj.rotation);
  mesh.castShadow = true;
  return mesh;
}

function makeSprite(text, color='#ffffff') {
  const canvas = document.createElement('canvas');
  canvas.width=300; canvas.height=72;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0,0,300,72);
  ctx.fillStyle='rgba(0,0,0,0.65)';
  ctx.roundRect(2,2,296,68,10);
  ctx.fill();
  ctx.fillStyle=color;
  ctx.font='bold 28px Inter,Arial,sans-serif';
  ctx.fillText(text,10,48);
  const tex = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true}));
  sprite.scale.set(3.5,0.9,1);
  sprite.position.set(0,1.4,0);
  return sprite;
}

function addAxes(scene) {
  [[[1,0,0],'#ef444488'],[[ 0,1,0],'#22c55e88'],[[0,0,1],'#3b82f688']].forEach(([d,c])=>{
    const pts=[new THREE.Vector3(0,0,0), new THREE.Vector3(...d).multiplyScalar(8)];
    scene.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({color:c,transparent:true,opacity:0.3})
    ));
  });
}
