import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Html, Stars } from '@react-three/drei';
import { Suspense, useRef, useState } from 'react';

// Shape component — NO useFrame scale animation (that was the enlargement bug)
function Shape({ s }) {
  const [hovered, setHovered] = useState(false);

  const getGeometry = () => {
    switch (s.shape) {
      case 'sphere':   return <sphereGeometry args={[0.5, 32, 32]} />;
      case 'cylinder': return <cylinderGeometry args={[0.5, 0.5, 1, 16]} />;
      case 'box':      return <boxGeometry args={[1, 1, 1]} />;
      case 'cone':     return <coneGeometry args={[0.5, 1, 16]} />;
      default:         return <sphereGeometry args={[0.5, 16, 16]} />;
    }
  };

  return (
    <mesh
      position={s.position}
      scale={s.scale}
      onPointerEnter={(e) => { e.stopPropagation(); setHovered(true); }}
      onPointerLeave={(e) => { e.stopPropagation(); setHovered(false); }}
    >
      {getGeometry()}
      <meshStandardMaterial
        color={hovered ? '#ffffff' : (s.color || '#4EA8DE')}
        metalness={0.1}
        roughness={0.55}
      />
      {s.label && (
        <Html distanceFactor={10} center style={{ pointerEvents: 'none' }}>
          <div style={{
            color: '#e6edf3',
            fontSize: 10,
            fontFamily: 'monospace',
            background: 'rgba(10,14,20,0.88)',
            padding: '2px 7px',
            borderRadius: 4,
            border: '1px solid rgba(78,168,222,0.35)',
            whiteSpace: 'nowrap',
            pointerEvents: 'none',
          }}>
            {s.label}
          </div>
        </Html>
      )}
    </mesh>
  );
}

// Slow auto-rotate — stops when user interacts
function SceneGeometry({ geometry }) {
  const groupRef = useRef();
  const rotating = useRef(true);

  useFrame((_, delta) => {
    if (groupRef.current && rotating.current) {
      groupRef.current.rotation.y += delta * 0.06;
    }
  });

  return (
    <group
      ref={groupRef}
      onPointerEnter={() => { rotating.current = false; }}
      onPointerLeave={() => { rotating.current = true; }}
    >
      {geometry.map((s, i) => <Shape key={i} s={s} />)}
    </group>
  );
}

function SpinningFallback() {
  const ref = useRef();
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 1.2;
  });
  return (
    <mesh ref={ref}>
      <octahedronGeometry args={[1.2]} />
      <meshStandardMaterial color="#0F9ED5" wireframe />
    </mesh>
  );
}

// Sketchfab embed in iframe
function SketchfabViewer({ url }) {
  return (
    <iframe
      title="Sketchfab 3D Model"
      src={url}
      allowFullScreen
      allow="autoplay; fullscreen; xr-spatial-tracking"
      style={{ width: '100%', height: '100%', border: 'none', display: 'block' }}
    />
  );
}

export function Viewer3D({ modelUrl, geometry, isSketchfab }) {
  // If Sketchfab model — render in iframe
  if (isSketchfab && modelUrl) {
    return (
      <div style={{
        width: '100%',
        height: 520,
        borderRadius: 16,
        overflow: 'hidden',
        border: '1px solid #2d3f5a',
        background: '#0d1117',
        position: 'relative',
      }}>
        <SketchfabViewer url={modelUrl} />
        <div style={{
          position: 'absolute', bottom: 10, right: 12,
          background: 'rgba(13,17,23,0.8)',
          color: '#4EA8DE', fontSize: 11, padding: '3px 8px',
          borderRadius: 6, border: '1px solid #2d3f5a',
          pointerEvents: 'none',
        }}>
          🌐 Sketchfab Model
        </div>
      </div>
    );
  }

  // Procedural / LLM geometry — render in Three.js canvas
  return (
    <div style={{
      width: '100%',
      height: 520,
      borderRadius: 16,
      overflow: 'hidden',
      border: '1px solid #2d3f5a',
      background: 'linear-gradient(135deg, #0d1117 0%, #0f1929 50%, #0a1628 100%)',
      position: 'relative',
    }}>
      <Canvas
        camera={{ position: [0, 4, 14], fov: 52 }}
        style={{ width: '100%', height: '100%' }}
        gl={{ antialias: true }}
      >
        <color attach="background" args={['#0d1117']} />
        <fog attach="fog" args={['#0d1117', 30, 70]} />

        <ambientLight intensity={0.45} />
        <directionalLight position={[10, 12, 6]} intensity={1.3} />
        <directionalLight position={[-6, -4, -4]} intensity={0.25} color="#4EA8DE" />
        <pointLight position={[0, 6, 2]} intensity={0.6} color="#156082" />

        <Stars radius={90} depth={40} count={1800} factor={3} fade speed={0.4} />

        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          minDistance={2}
          maxDistance={50}
          dampingFactor={0.08}
          enableDamping
        />

        <Suspense fallback={<SpinningFallback />}>
          {geometry && <SceneGeometry geometry={geometry} />}
        </Suspense>
      </Canvas>

      <div style={{
        position: 'absolute', bottom: 12, right: 14,
        color: '#3a4a5a', fontSize: 11, fontFamily: 'monospace',
        display: 'flex', gap: 12, pointerEvents: 'none',
      }}>
        <span>drag · rotate</span>
        <span>scroll · zoom</span>
      </div>
    </div>
  );
}