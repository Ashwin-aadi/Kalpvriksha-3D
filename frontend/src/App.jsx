import { useState } from 'react';
import { Home } from './pages/Home.jsx';
import { MathGrapher } from './components/MathGrapher/MathGrapher.jsx';
import { PhysicsEngine } from './components/PhysicsEngine/PhysicsEngine.jsx';
import { ModeWheel } from './components/ModeWheel.jsx';

export default function App() {
  const [mode, setMode] = useState('concept'); // 'concept' | 'math' | 'physics'

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#0a0a0f', position: 'relative' }}>
      {mode === 'concept' && <Home />}
      {mode === 'math'    && <MathGrapher />}
      {mode === 'physics' && <PhysicsEngine />}
      <ModeWheel currentMode={mode} onModeChange={setMode} />
    </div>
  );
}
