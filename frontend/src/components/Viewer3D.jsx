import { Canvas } from '@react-three/fiber';
import { OrbitControls, useGLTF, Html, Stars } from '@react-three/drei';
import { Suspense, useRef } from 'react';
import { useFrame } from '@react-three/fiber';

function GLBModel({ url }) {
  const { scene } = useGLTF(url);
  return <primitive object={scene} />;
}

function RotatingGroup({ children }) {
  const ref = useRef();
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 0.3;
  });
  return <group ref={ref}>{children}</group>;
}

function Shape({ s }) {
  // Flat disc detection: cylinder with very small height scale → render as torus ring
  const isFlatDisc = s.shape === 'cylinder' && s.scale && s.scale[1] <= 0.05;

  let geo;
  if (s.shape === 'sphere') {
    geo = <sphereGeometry args={[0.5, 32, 32]} />;
  } else if (s.shape === 'cone') {
    geo = <coneGeometry args={[0.5, 1, 16]} />;
  } else if (s.shape === 'cylinder') {
    if (isFlatDisc) {
      const ringRadius = s.scale[0] / 2;
      const tube = Math.max(0.02, ringRadius * 0.015);
      geo = <torusGeometry args={[ringRadius, tube, 8, 64]} />;
    } else {
      geo = <cylinderGeometry args={[0.5, 0.5, 1, 16]} />;
    }
  } else {
    geo = <boxGeometry args={[1, 1, 1]} />;
  }

  const meshScale = isFlatDisc ? [1, 1, 1] : s.scale;
  const isTransparent = s.color === '#AED6F1' || s.color === '#aed6f1';

  return (
    <mesh position={s.position} scale={meshScale}>
      {geo}
      <meshStandardMaterial
        color={s.color}
        roughness={0.3}
        metalness={0.2}
        transparent={isTransparent}
        opacity={isTransparent ? 0.3 : 1.0}
      />
      {s.label && (
        <Html distanceFactor={6} center>
          <div style={{
            color: '#fff',
            fontSize: 11,
            background: 'rgba(0,0,0,.75)',
            padding: '2px 8px',
            borderRadius: 4,
            whiteSpace: 'nowrap',
            border: '1px solid rgba(255,255,255,0.15)',
            backdropFilter: 'blur(4px)',
            pointerEvents: 'none',
          }}>
            {s.label}
          </div>
        </Html>
      )}
    </mesh>
  );
}

export function Viewer3D({ modelUrl, geometry }) {
  return (
    <div style={{
      width: '100%',
      height: 460,
      background: 'linear-gradient(160deg, #0d1117 0%, #161b22 100%)',
      borderRadius: 16,
      overflow: 'hidden',
      border: '1px solid #30363d',
    }}>
      <Canvas camera={{ position: [0, 3, 10], fov: 60 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1.2} />
        <pointLight position={[-10, -10, -5]} intensity={0.4} color="#4EA8DE" />
        <OrbitControls enablePan enableZoom enableRotate makeDefault />
        <Stars radius={80} depth={50} count={3000} factor={4} fade speed={1} />
        <Suspense fallback={null}>
          {modelUrl && <GLBModel url={modelUrl} />}
          {geometry && (
            <RotatingGroup>
              {geometry.map((s, i) => <Shape key={i} s={s} />)}
            </RotatingGroup>
          )}
          {!modelUrl && !geometry && (
            <mesh>
              <sphereGeometry args={[1.5, 32, 32]} />
              <meshStandardMaterial color="#156082" wireframe />
            </mesh>
          )}
        </Suspense>
      </Canvas>
    </div>
  );
}
