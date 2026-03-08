import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import * as THREE from 'three';

const DEFAULT_SPH = { theta: Math.PI / 4, phi: Math.PI / 3, radius: 22 };

function cameraPreset(type) {
  const t = (type || '').toLowerCase();
  if (['lens','mirror','prism','refraction','slit','optics','diffraction','interference'].some(k=>t.includes(k)))
    return { theta: Math.PI/2, phi: Math.PI/2, radius: 18 };
  if (['wave','doppler','lc_','em_','bohr','photo','pv_','carnot','radioact'].some(k=>t.includes(k)))
    return { theta: Math.PI/2, phi: Math.PI/2.3, radius: 20 };
  if (['electric','magnetic','cyclotron'].some(k=>t.includes(k)))
    return { theta: Math.PI/2, phi: Math.PI/2.5, radius: 18 };
  return { ...DEFAULT_SPH };
}

function shouldHideGrid(type) {
  const t = (type||'').toLowerCase();
  return ['lens','mirror','prism','refraction','slit','optics','wave','doppler',
          'lc_','em_','bohr','photo','carnot','radioact','electric','magnetic'].some(k=>t.includes(k));
}

const FBD_MAP = {
  projectile:      [['#ef4444','mg','Weight ↓'],['#22c55e','v₀','Initial velocity'],['#60a5fa','vₓ','Horizontal component'],['#f59e0b','vᵧ','Vertical component']],
  free_fall:       [['#ef4444','mg','Weight / Gravity ↓']],
  pendulum:        [['#60a5fa','T','Tension along string'],['#ef4444','mg','Weight ↓']],
  block_on_incline:[['#22c55e','N','Normal force ⊥ surface'],['#ef4444','mg','Weight ↓'],['#f59e0b','f','Friction force']],
  spring:          [['#10b981','Fₛ','Spring restoring force'],['#ef4444','mg','Weight ↓'],['#22c55e','N','Normal force']],
  shm:             [['#10b981','Fₛ','Spring restoring force'],['#ef4444','mg','Weight ↓']],
  atwood:          [['#60a5fa','T','Tension (equal both sides)'],['#ef4444','mg','Weight on each mass']],
  vertical_circle: [['#60a5fa','T','Tension (centripetal)'],['#ef4444','mg','Weight ↓'],['#8b5cf6','Fc','Centripetal force']],
  collision:       [['#3b82f6','p₁','Momentum of m₁'],['#ef4444','p₂','Momentum of m₂']],
  rolling:         [['#ef4444','mg','Weight ↓'],['#22c55e','N','Normal force'],['#f59e0b','f','Static friction']],
};

function getFBDLegend(type) {
  const t = (type||'').toLowerCase();
  const key = Object.keys(FBD_MAP).find(k => t.includes(k));
  return key ? FBD_MAP[key] : [];
}

function drawFBDArrows(scene, type) {
  const t = (type||'').toLowerCase();
  const arr = (ox,oy,oz,dx,dy,dz,color) => {
    const dir=new THREE.Vector3(dx,dy,dz); const len=dir.length(); if(len<0.05) return;
    const a=new THREE.ArrowHelper(dir.normalize(),new THREE.Vector3(ox,oy,oz),
      Math.max(0.7,Math.min(len,3)),color,0.28,0.12);
    a.userData.isSim=true; scene.add(a);
  };
  if      (t.includes('projectile'))      { arr(0,1,0,0,-2,0,'#ef4444');arr(0,1,0,2,2,0,'#22c55e');arr(0,1,0,2,0,0,'#60a5fa');arr(0,1,0,0,2,0,'#f59e0b'); }
  else if (t.includes('free_fall'))       { arr(0,3,0,0,-2.5,0,'#ef4444'); }
  else if (t.includes('pendulum'))        { arr(0,2,0,-0.6,2.4,0,'#60a5fa');arr(0,2,0,0,-2,0,'#ef4444'); }
  else if (t.includes('incline'))         { arr(2,2,0,0.6,1.8,0,'#22c55e');arr(2,2,0,0,-2.5,0,'#ef4444');arr(2,2,0,-1.5,0.5,0,'#f59e0b'); }
  else if (t.includes('spring')||t.includes('shm')) { arr(0,0.8,0,-2,0,0,'#10b981');arr(0,0.8,0,0,-1.5,0,'#ef4444');arr(0,0.8,0,0,1.5,0,'#22c55e'); }
  else if (t.includes('atwood'))          { arr(-0.5,3,0,0,1.5,0,'#60a5fa');arr(-0.5,3,0,0,-2.5,0,'#ef4444');arr(0.5,2,0,0,1.5,0,'#60a5fa');arr(0.5,2,0,0,-1.5,0,'#ef4444'); }
  else if (t.includes('vertical_c'))     { arr(0,-1,0,0,3,0,'#60a5fa');arr(0,-1,0,0,-2,0,'#ef4444');arr(0,3,0,0,-1.5,0,'#8b5cf6'); }
  else if (t.includes('collision'))       { arr(-5,0.5,0,2.5,0,0,'#3b82f6');arr(5,0.5,0,-1.5,0,0,'#ef4444'); }
}

function generateFallbackKeyframes(type, solution) {
  const t = (type||'').toLowerCase();
  const get = k => {
    if (!solution) return null;
    const key=Object.keys(solution).find(s=>s.toLowerCase().includes(k.toLowerCase()));
    return key ? parseFloat(solution[key]) : null;
  };

  if (t.includes('projectile')) {
    const vx=get('vx')||15, vy=get('vy')||20, g=9.8;
    const totalT=Math.abs(2*vy/g)+0.5;
    const frames=[];
    for(let i=0;i<=50;i++){
      const time=i*(totalT/50);
      frames.push({t:time, x:vx*time*0.4-5, y:Math.max(0,vy*time-0.5*g*time*time)*0.3, z:0});
    }
    return [{id:'ball',shape:'sphere',size:0.35,color:'#f59e0b',trail:true,loop:false,keyframes:frames}];
  }
  if (t.includes('free_fall')) {
    const h=get('height')||20, g=9.8;
    const totalT=Math.sqrt(2*h/g);
    const frames=[];
    for(let i=0;i<=40;i++){
      const time=i*(totalT/40);
      frames.push({t:time, x:0, y:8-0.5*g*time*time*0.2, z:0});
    }
    return [{id:'stone',shape:'sphere',size:0.3,color:'#888',trail:true,loop:false,keyframes:frames}];
  }
  if (t.includes('pendulum')) {
    const L=get('length')||1.5, angle=get('angle')||45;
    const T_p=2*Math.PI*Math.sqrt(L/9.8);
    const frames=[];
    for(let i=0;i<=80;i++){
      const time=i*(T_p*2/80);
      const theta=(angle*Math.PI/180)*Math.cos(2*Math.PI*time/T_p);
      frames.push({t:time, x:Math.sin(theta)*L*4, y:5-Math.cos(theta)*L*4, z:0});
    }
    return [
      {id:'string_top',shape:'sphere',size:0.15,color:'#555',loop:true,keyframes:[{t:0,x:0,y:5,z:0},{t:99,x:0,y:5,z:0}]},
      {id:'bob',shape:'sphere',size:0.35,color:'#f59e0b',loop:true,keyframes:frames},
    ];
  }
  if (t.includes('spring')||t.includes('shm')) {
    const A=Math.max(0.05,get('amplitude')||0.1), T_p=Math.max(0.2,get('period')||0.5);
    const amp=Math.min(A*40,5);
    const frames=[];
    for(let i=0;i<=80;i++){
      const time=i*(T_p*2/80);
      frames.push({t:time, x:amp*Math.cos(2*Math.PI*time/T_p), y:1, z:0});
    }
    return [{id:'mass',shape:'box',size:0.6,color:'#6366f1',loop:true,keyframes:frames}];
  }
  if (t.includes('vertical_c')||t.includes('vertical circle')) {
    const R=Math.max(1,get('radius')||2)*1.5;
    const frames=[];
    for(let i=0;i<=80;i++){
      const angle=i*(2*Math.PI/80);
      frames.push({t:i*0.08, x:R*Math.sin(angle), y:R+R-R*Math.cos(angle), z:0});
    }
    return [{id:'ball',shape:'sphere',size:0.3,color:'#f59e0b',loop:true,keyframes:frames}];
  }
  if (t.includes('atwood')) {
    const a=Math.min(get('acceleration')||2,5);
    return [
      {id:'m1',shape:'box',size:0.6,color:'#ef4444',loop:false,keyframes:[{t:0,x:-1.2,y:5,z:0},{t:3,x:-1.2,y:5+a*4.5*0.5,z:0}]},
      {id:'m2',shape:'box',size:0.5,color:'#22c55e',loop:false,keyframes:[{t:0,x:1.2,y:4,z:0},{t:3,x:1.2,y:4-a*4.5*0.5,z:0}]},
    ];
  }
  if (t.includes('collision')) {
    const v1f=get('v1_final')||(-2), v2f=get('v2_final')||(6);
    return [
      {id:'m1',shape:'sphere',size:0.55,color:'#3b82f6',loop:false,keyframes:[{t:0,x:-8,y:0.5,z:0},{t:1.5,x:0,y:0.5,z:0},{t:4,x:v1f*0.5,y:0.5,z:0}]},
      {id:'m2',shape:'sphere',size:0.45,color:'#ef4444',loop:false,keyframes:[{t:0,x:0.5,y:0.5,z:0},{t:1.5,x:0.5,y:0.5,z:0},{t:4,x:0.5+v2f*0.5,y:0.5,z:0}]},
    ];
  }
  if (t.includes('wave')||t.includes('interference')||t.includes('resonance')) {
    const objs=[];
    for(let i=0;i<12;i++){
      const frames=[], x=i*1.2-7;
      for(let j=0;j<=60;j++){
        const time=j*0.08;
        frames.push({t:time, x, y:2*Math.sin(i*0.5-time*3)+1.5*Math.sin(i*0.8-time*2), z:0});
      }
      objs.push({id:`w${i}`,shape:'sphere',size:0.12,color:'#10b981',loop:true,keyframes:frames});
    }
    return objs;
  }
  if (t.includes('doppler')) {
    // Source moving + waves
    const objs=[];
    const frames=[];
    for(let i=0;i<=60;i++){frames.push({t:i*0.1, x:-6+i*0.2, y:1, z:0});}
    objs.push({id:'source',shape:'sphere',size:0.4,color:'#ef4444',loop:false,keyframes:frames});
    for(let w=0;w<5;w++){
      const wf=[], startX=-3+w*1.5;
      for(let i=0;i<=60;i++){
        const time=i*0.1;
        wf.push({t:time, x:startX+Math.sin(time*4+w)*2, y:1+Math.cos(time*4+w)*2, z:0});
      }
      objs.push({id:`wave${w}`,shape:'sphere',size:0.08,color:'#10b98188',loop:true,keyframes:wf});
    }
    return objs;
  }
  if (t.includes('lc_')||t.includes('lc circuit')||t.includes('damped')) {
    const T_p=Math.max(0.01,get('period')||0.02), maxI=6;
    const frames=[];
    for(let i=0;i<=80;i++){
      const time=i*(T_p*4/80);
      const decay=Math.exp(-time*0.3);
      frames.push({t:time, x:Math.cos(2*Math.PI*time/T_p)*maxI*decay, y:Math.sin(2*Math.PI*time/T_p)*maxI*decay+1, z:0});
    }
    return [{id:'charge',shape:'sphere',size:0.4,color:'#3b82f6',trail:true,loop:false,keyframes:frames}];
  }
  if (t.includes('em_')||t.includes('induction')) {
    const frames=[];
    for(let i=0;i<=80;i++){
      const time=i*0.05;
      frames.push({t:time, x:Math.cos(time*3)*5, y:Math.sin(time*3)*3+3, z:0});
    }
    return [{id:'coil',shape:'disk_3d',radius:1.2,color:'#3b82f6',loop:true,keyframes:frames}];
  }
  if (t.includes('magnetic')||t.includes('cyclotron')) {
    const r=Math.max(1,get('radius')||2)*1.5;
    const frames=[];
    for(let i=0;i<=80;i++){
      const angle=i*(2*Math.PI/80);
      frames.push({t:i*0.05, x:r*Math.cos(angle), y:r*Math.sin(angle)+r, z:0});
    }
    return [{id:'particle',shape:'sphere',size:0.25,color:'#ec4899',trail:true,loop:true,keyframes:frames}];
  }
  if (t.includes('electric')) {
    // Two charges attracting/repelling
    return [
      {id:'q1',shape:'sphere',size:0.5,color:'#ef4444',loop:true,keyframes:[{t:0,x:-4,y:1,z:0},{t:2,x:-3,y:1,z:0},{t:4,x:-4,y:1,z:0}]},
      {id:'q2',shape:'sphere',size:0.5,color:'#3b82f6',loop:true,keyframes:[{t:0,x:4,y:1,z:0},{t:2,x:3,y:1,z:0},{t:4,x:4,y:1,z:0}]},
    ];
  }
  if (t.includes('bohr')) {
    const n=get('n')||3;
    const objs=[];
    objs.push({id:'nucleus',shape:'sphere',size:0.4,color:'#ef4444',loop:true,keyframes:[{t:0,x:0,y:0,z:0},{t:999,x:0,y:0,z:0}]});
    for(let level=1;level<=n;level++){
      const r=level*2.5, T_p=level*0.5;
      const frames=[];
      for(let i=0;i<=80;i++){
        const angle=i*(2*Math.PI/80);
        frames.push({t:i*(T_p/80), x:r*Math.cos(angle), y:r*Math.sin(angle), z:0});
      }
      objs.push({id:`e${level}`,shape:'sphere',size:0.18,color:level===n?'#fbbf24':'#3b82f6',loop:true,keyframes:frames});
    }
    return objs;
  }
  if (t.includes('photo')) {
    return [
      {id:'photon',shape:'sphere',size:0.2,color:'#fbbf24',trail:true,loop:false,keyframes:[{t:0,x:-7,y:2,z:0},{t:2,x:0,y:0,z:0}]},
      {id:'electron',shape:'sphere',size:0.25,color:'#3b82f6',trail:true,loop:false,keyframes:[{t:2,x:0,y:0,z:0},{t:4,x:5,y:4,z:0}]},
    ];
  }
  if (t.includes('radioact')) {
    const hl=Math.max(1,get('half_life')||10);
    const objs=[];
    for(let i=0;i<8;i++){
      const px=(i%4)*2.5-3.5, py=Math.floor(i/4)*2.5;
      objs.push({id:`atom${i}`,shape:'sphere',size:0.5,color:'#ec4899',loop:false,
        keyframes:[{t:0,x:px,y:py,z:0},{t:hl*i*0.12,x:px,y:py,z:0},{t:hl*i*0.12+0.5,x:px,y:py+10,z:0}]});
    }
    return objs;
  }
  if (t.includes('carnot')||t.includes('isothermal')||t.includes('adiabatic')||t.includes('isobaric')) {
    const frames=[];
    for(let i=0;i<=80;i++){
      const time=i*0.1;
      frames.push({t:time, x:Math.cos(time*0.8)*2, y:2+Math.sin(time*0.8)*1.5, z:0});
    }
    return [
      {id:'piston',shape:'box',size:0.9,height_ratio:0.3,color:'#888',loop:true,keyframes:frames},
      {id:'gas',shape:'sphere',size:0.4,color:'#ef4444',loop:true,
        keyframes:frames.map(f=>({...f,x:f.x*0.5,y:f.y-0.5}))},
    ];
  }
  if (t.includes('calorimetry')) {
    return [
      {id:'hot',shape:'box',size:1,color:'#ef4444',loop:true,
        keyframes:[{t:0,x:-2,y:0,z:0},{t:5,x:-2,y:0,z:0}]},
      {id:'cold',shape:'box',size:0.8,color:'#3b82f6',loop:true,
        keyframes:[{t:0,x:2,y:0,z:0},{t:5,x:2,y:0,z:0}]},
      {id:'mix',shape:'sphere',size:0.2,color:'#f59e0b',loop:true,
        keyframes:[{t:0,x:-2,y:1,z:0},{t:2,x:0,y:1.5,z:0},{t:5,x:2,y:1,z:0}]},
    ];
  }
  if (t.includes('heat_conduction')||t.includes('conduction')) {
    const objs=[];
    for(let i=0;i<10;i++){
      const startColor=i<5?'#ef4444':'#3b82f6';
      const x=i*1.2-5;
      objs.push({id:`node${i}`,shape:'sphere',size:0.35,color:startColor,loop:true,
        keyframes:[{t:0,x,y:0,z:0},{t:5,x,y:0,z:0}]});
    }
    return objs;
  }
  if (t.includes('refraction')||t.includes('snell')||t.includes('optics')) {
    return [
      {id:'ray',shape:'sphere',size:0.15,color:'#fbbf24',trail:true,loop:false,
       keyframes:[{t:0,x:-7,y:4,z:0},{t:2,x:0,y:0,z:0},{t:4,x:5,y:-2,z:0}]},
    ];
  }
  if (t.includes('lens')||t.includes('mirror')) {
    return [
      {id:'ray1',shape:'sphere',size:0.12,color:'#fbbf24',trail:true,loop:false,
       keyframes:[{t:0,x:-8,y:2,z:0},{t:2,x:0,y:2,z:0},{t:4,x:4,y:-1,z:0}]},
      {id:'ray2',shape:'sphere',size:0.12,color:'#f59e0b',trail:true,loop:false,
       keyframes:[{t:0,x:-8,y:0,z:0},{t:2,x:0,y:0,z:0},{t:4,x:4,y:0,z:0}]},
      {id:'ray3',shape:'sphere',size:0.12,color:'#fcd34d',trail:true,loop:false,
       keyframes:[{t:0,x:-8,y:-2,z:0},{t:2,x:0,y:-2,z:0},{t:4,x:4,y:1,z:0}]},
    ];
  }
  if (t.includes('slit')||t.includes('young')||t.includes('diffraction')) {
    const objs=[];
    for(let i=-4;i<=4;i++){
      const frames=[];
      for(let j=0;j<=60;j++){
        const time=j*0.1;
        frames.push({t:time, x:i*1.5+time*2, y:Math.sin(time*3+i*0.7)*2, z:0});
      }
      objs.push({id:`fringe${i+4}`,shape:'sphere',size:0.1,
        color:i%2===0?'#fbbf24':'#fbbf2455',loop:true,keyframes:frames});
    }
    return objs;
  }
  if (t.includes('rolling')||t.includes('rotation')) {
    const frames=[];
    for(let i=0;i<=60;i++){
      frames.push({t:i*0.1, x:i*0.15-4, y:0.5, z:i*0.3});
    }
    return [{id:'cylinder',shape:'disk_3d',radius:0.5,color:'#6366f1',loop:false,isRotating:true,keyframes:frames}];
  }
  // Generic fallback
  return [{id:'obj',shape:'sphere',size:0.5,color:'#6366f1',loop:true,
    keyframes:[{t:0,x:-3,y:1,z:0},{t:2,x:3,y:3,z:0},{t:4,x:-3,y:1,z:0}]}];
}

export const SimCanvas = forwardRef(function SimCanvas({ simData, playing, loading }, ref) {
  const mountRef    = useRef(null);
  const sceneRef    = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef   = useRef(null);
  const frameRef    = useRef(null);
  const clockRef    = useRef(new THREE.Clock());
  const animRef     = useRef([]);
  const playingRef  = useRef(false);
  const spherical   = useRef({ ...DEFAULT_SPH });
  const target      = useRef(new THREE.Vector3(0,0,0));
  const isDragging  = useRef(false);
  const prevMouse   = useRef({ x:0, y:0 });
  const keysHeld    = useRef({});
  const labelDivs   = useRef([]);
  const keyLoopRef  = useRef(null);
  const gridRef     = useRef(null);
  const simDataRef  = useRef(null);

  playingRef.current = playing;
  simDataRef.current = simData;

  // Expose restart() to parent — NO remount, NO camera change
  useImperativeHandle(ref, () => ({
    restart() {
      clockRef.current = new THREE.Clock();
      animRef.current.forEach(obj => {
        if (obj.trailPoints) obj.trailPoints.length = 0;
        if (obj.trailLine && sceneRef.current) {
          sceneRef.current.remove(obj.trailLine);
          obj.trailLine.geometry.dispose();
          obj.trailLine = null;
        }
        if (obj.keyframes?.length > 0) {
          const kf = obj.keyframes[0];
          obj.mesh.position.set(kf.x||0, kf.y||0, kf.z||0);
        }
      });
      // Camera angle intentionally NOT touched
    }
  }));

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#080810');
    sceneRef.current = scene;
    const camera = new THREE.PerspectiveCamera(55, mount.clientWidth/mount.clientHeight, 0.01, 1000);
    cameraRef.current = camera;
    updateCamera();
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;
    const grid = new THREE.GridHelper(40,40,'#1a1a2a','#0f0f1a');
    grid.material.transparent=true; grid.material.opacity=0.4;
    scene.add(grid); gridRef.current=grid;
    addAxes(scene);
    scene.add(new THREE.AmbientLight('#ffffff',0.6));
    const sun = new THREE.DirectionalLight('#ffffff',1);
    sun.position.set(10,20,10); sun.castShadow=true; scene.add(sun);

    const onDown  = e => { isDragging.current=true; prevMouse.current={x:e.clientX,y:e.clientY}; };
    const onUp    = () => { isDragging.current=false; };
    const onMove  = e => {
      if (!isDragging.current) return;
      spherical.current.theta -= (e.clientX-prevMouse.current.x)*0.007;
      spherical.current.phi    = Math.max(0.05,Math.min(Math.PI-0.05,
        spherical.current.phi-(e.clientY-prevMouse.current.y)*0.007));
      prevMouse.current={x:e.clientX,y:e.clientY}; updateCamera();
    };
    const onWheel = e => {
      e.preventDefault();
      spherical.current.radius=Math.max(1.5,Math.min(120,spherical.current.radius+e.deltaY*0.03));
      updateCamera();
    };
    const onKeyDown = e => {
      const tag=document.activeElement.tagName.toLowerCase();
      if (tag==='input'||tag==='textarea') return;
      keysHeld.current[e.key.toLowerCase()]=true;
      if (e.key.toLowerCase()==='r') {
        spherical.current=cameraPreset(simDataRef.current?.problem_type);
        target.current.set(0,0,0); updateCamera();
      }
    };
    const onKeyUp = e => { delete keysHeld.current[e.key.toLowerCase()]; };

    mount.addEventListener('mousedown',onDown);
    mount.addEventListener('mouseup',onUp);
    window.addEventListener('mouseup',onUp);
    mount.addEventListener('mousemove',onMove);
    mount.addEventListener('wheel',onWheel,{passive:false});
    window.addEventListener('keydown',onKeyDown);
    window.addEventListener('keyup',onKeyUp);

    const keyLoop = () => {
      const k=keysHeld.current;
      if(!Object.keys(k).length){keyLoopRef.current=requestAnimationFrame(keyLoop);return;}
      const {radius}=spherical.current; const spd=radius*0.025;
      const t=target.current; const camPos=camera.position;
      const fwd=new THREE.Vector3(t.x-camPos.x,0,t.z-camPos.z).normalize();
      const rgt=new THREE.Vector3().crossVectors(fwd,new THREE.Vector3(0,1,0)).normalize();
      if(k['w']||k['arrowup'])   {t.x+=fwd.x*spd;t.z+=fwd.z*spd;}
      if(k['s']||k['arrowdown']) {t.x-=fwd.x*spd;t.z-=fwd.z*spd;}
      if(k['a']||k['arrowleft']) {t.x-=rgt.x*spd;t.z-=rgt.z*spd;}
      if(k['d']||k['arrowright']){t.x+=rgt.x*spd;t.z+=rgt.z*spd;}
      if(k['e'])t.y+=spd; if(k['q'])t.y-=spd;
      updateCamera(); keyLoopRef.current=requestAnimationFrame(keyLoop);
    };
    keyLoopRef.current=requestAnimationFrame(keyLoop);

    const animate = () => {
      frameRef.current=requestAnimationFrame(animate);
      if (playingRef.current) {
        const elapsed=clockRef.current.getElapsedTime();
        animRef.current.forEach(obj=>{
          const {mesh,keyframes,loop,trailPoints,isRotating}=obj;
          if(!keyframes||keyframes.length<2) return;
          const dur=keyframes[keyframes.length-1].t; if(dur<=0) return;
          const ct=loop?elapsed%dur:Math.min(elapsed,dur);
          let i=0;
          while(i<keyframes.length-2&&keyframes[i+1].t<=ct)i++;
          const k0=keyframes[i],k1=keyframes[Math.min(i+1,keyframes.length-1)];
          const a=k1.t===k0.t?0:(ct-k0.t)/(k1.t-k0.t);
          const nx=k0.x+(k1.x-k0.x)*a, ny=k0.y+(k1.y-k0.y)*a, nz=(k0.z||0)+((k1.z||0)-(k0.z||0))*a;
          mesh.position.set(nx,ny,nz);
          if(isRotating) mesh.rotation.y=elapsed*2;
          if(trailPoints){
            trailPoints.push(new THREE.Vector3(nx,ny,nz));
            if(trailPoints.length>500) trailPoints.shift();
            if(obj.trailLine){scene.remove(obj.trailLine);obj.trailLine.geometry.dispose();}
            if(trailPoints.length>1){
              const tl=new THREE.Line(new THREE.BufferGeometry().setFromPoints(trailPoints),
                new THREE.LineBasicMaterial({color:'#f59e0b',transparent:true,opacity:0.6}));
              obj.trailLine=tl; scene.add(tl);
            }
          }
        });
      }
      renderer.render(scene,camera);
      labelDivs.current.forEach(d=>{
        if(!d._pos||!d.isConnected) return;
        const rect=renderer.domElement.getBoundingClientRect();
        const v=d._pos.clone().project(camera);
        d.style.left=((v.x+1)/2*rect.width)+'px';
        d.style.top=((1-v.y)/2*rect.height-22)+'px';
        d.style.display=v.z<1?'block':'none';
      });
    };
    animate();

    const onResize=()=>{
      camera.aspect=mount.clientWidth/mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth,mount.clientHeight);
    };
    window.addEventListener('resize',onResize);

    return ()=>{
      cancelAnimationFrame(frameRef.current);
      cancelAnimationFrame(keyLoopRef.current);
      mount.removeEventListener('mousedown',onDown);
      mount.removeEventListener('mouseup',onUp);
      window.removeEventListener('mouseup',onUp);
      mount.removeEventListener('mousemove',onMove);
      mount.removeEventListener('wheel',onWheel);
      window.removeEventListener('keydown',onKeyDown);
      window.removeEventListener('keyup',onKeyUp);
      window.removeEventListener('resize',onResize);
      labelDivs.current.forEach(d=>{if(d.isConnected)d.remove();});
      labelDivs.current=[];
      if(mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, []);

  useEffect(()=>{
    if(!sceneRef.current) return;
    const scene=sceneRef.current;
    animRef.current.forEach(obj=>{
      scene.remove(obj.mesh);
      if(obj.mesh.geometry) obj.mesh.geometry.dispose();
      if(obj.trailLine){scene.remove(obj.trailLine);obj.trailLine.geometry.dispose();}
    });
    animRef.current=[];
    scene.children.filter(c=>c.userData.isSim).forEach(c=>{scene.remove(c);if(c.geometry)c.geometry.dispose();});
    labelDivs.current.forEach(d=>{if(d.isConnected)d.remove();});
    labelDivs.current=[];
    if(!simData) return;
    clockRef.current=new THREE.Clock();
    spherical.current=cameraPreset(simData.problem_type);
    target.current.set(0,0,0);
    updateCamera();
    if(gridRef.current) gridRef.current.visible=!shouldHideGrid(simData.problem_type);

    const {static_objects=[],vectors=[],lines=[],scene_labels=[]}=simData;
    let {objects=[]}=simData;

    // If backend gave no animated objects or no keyframes, use frontend fallbacks
    const hasKeyframes=objects.some(o=>o.keyframes?.length>=2);
    if(!hasKeyframes) {
      objects=generateFallbackKeyframes(simData.problem_type,simData.solution);
    }

    static_objects.forEach(obj=>{const m=buildMesh(obj);if(m){m.userData.isSim=true;scene.add(m);}});

    objects.forEach(obj=>{
      const m=buildMesh(obj); if(!m) return;
      const entry={mesh:m,keyframes:obj.keyframes||[],loop:obj.loop!==false,
        trailPoints:obj.trail?[]:null,trailLine:null,isRotating:!!obj.isRotating};
      if(entry.keyframes.length>0){const kf=entry.keyframes[0];m.position.set(kf.x||0,kf.y||0,kf.z||0);}
      scene.add(m); animRef.current.push(entry);
    });

    vectors.forEach(v=>{
      if(!v?.origin||!v?.direction) return;
      const dir=new THREE.Vector3(...v.direction); const len=dir.length(); if(len<0.001) return;
      dir.normalize();
      const arrow=new THREE.ArrowHelper(dir,new THREE.Vector3(...v.origin),
        Math.max(0.4,Math.min(len,7)),v.color||'#f59e0b',Math.min(0.4,len*0.25),0.15);
      arrow.userData.isSim=true; scene.add(arrow);
      if(v.label) addLabel(new THREE.Vector3(...v.origin).add(dir.clone().multiplyScalar(len+0.6)),v.label,v.color||'#f59e0b');
    });

    lines.forEach(ld=>{
      if(!ld?.points||ld.points.length<2) return;
      const pts=ld.points.map(p=>new THREE.Vector3(p[0],p[1],p[2]||0));
      const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
        new THREE.LineBasicMaterial({color:ld.color||'#fff',transparent:true,opacity:ld.dashed?0.3:0.9}));
      line.userData.isSim=true; scene.add(line);
      if(!ld.dashed&&pts.length>=2){
        const last=pts[pts.length-1],prev=pts[pts.length-2],d=last.clone().sub(prev);
        if(d.length()>0.01){const ah=new THREE.ArrowHelper(d.normalize(),last,0.001,ld.color||'#fff',0.4,0.18);ah.userData.isSim=true;scene.add(ah);}
      }
      if(ld.label) addLabel(pts[Math.floor(pts.length/2)].clone().add(new THREE.Vector3(0,0.6,0)),ld.label,ld.color||'#aaa');
    });

    scene_labels.forEach(lb=>{
      if(!lb?.text?.trim()) return;
      addLabel(new THREE.Vector3(lb.x||0,lb.y||0,lb.z||0),lb.text,lb.color||'#aaa');
    });

    drawFBDArrows(scene,simData.problem_type);
  },[simData]);

  function addLabel(pos,text,color){
    const mount=mountRef.current; if(!mount) return;
    const div=document.createElement('div');
    div.style.cssText=`position:absolute;pointer-events:none;font-size:12px;font-weight:700;
      font-family:'Inter',sans-serif;color:${color};background:rgba(4,4,14,0.92);
      padding:2px 9px;border-radius:5px;border:1px solid ${color}55;
      white-space:nowrap;z-index:12;transform:translateX(-50%);text-shadow:0 1px 3px #000;`;
    div.textContent=text; div._pos=pos.clone();
    mount.appendChild(div); labelDivs.current.push(div);
  }

  function updateCamera(){
    if(!cameraRef.current) return;
    const {theta,phi,radius}=spherical.current; const t=target.current;
    cameraRef.current.position.set(
      t.x+radius*Math.sin(phi)*Math.cos(theta),
      t.y+radius*Math.cos(phi),
      t.z+radius*Math.sin(phi)*Math.sin(theta));
    cameraRef.current.lookAt(t);
  }

  const fbdLegend=getFBDLegend(simData?.problem_type);
  const objLegend=(simData?.objects||[]).filter(o=>o.label||o.id);

  return (
    <div ref={mountRef} style={{width:'100%',height:'100%',position:'relative',overflow:'hidden'}}>
      {loading&&(<div style={{position:'absolute',inset:0,display:'flex',flexDirection:'column',
        alignItems:'center',justifyContent:'center',background:'rgba(5,5,15,0.93)',zIndex:20,gap:14}}>
        <div style={{fontSize:38,animation:'spin 0.8s linear infinite'}}>⚡</div>
        <div style={{color:'#f59e0b',fontSize:15,fontWeight:700}}>Solving & animating...</div>
        <div style={{color:'#555',fontSize:12}}>LLM → solver → 3D scene</div>
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      </div>)}
      {!simData&&!loading&&(<div style={{position:'absolute',inset:0,display:'flex',flexDirection:'column',
        alignItems:'center',justifyContent:'center',pointerEvents:'none',gap:10}}>
        <div style={{fontSize:52,opacity:0.09}}>⚡</div>
        <div style={{color:'#2a2a2a',fontSize:14}}>Select a chapter and describe a problem</div>
      </div>)}
      {simData&&fbdLegend.length>0&&(<div style={{position:'absolute',top:14,left:14,
        background:'rgba(4,4,14,0.92)',border:'1px solid #1e1e2e',borderRadius:10,
        padding:'10px 14px',zIndex:15,pointerEvents:'none'}}>
        <div style={{color:'#444',fontSize:10,fontWeight:700,letterSpacing:'0.08em',marginBottom:7}}>FREE BODY DIAGRAM</div>
        {fbdLegend.map(([color,sym,desc])=>(
          <div key={sym} style={{display:'flex',alignItems:'center',gap:8,marginBottom:5}}>
            <div style={{width:20,height:3,background:color,borderRadius:2,flexShrink:0}}/>
            <span style={{color:'#aaa',fontSize:11}}><span style={{color,fontWeight:700}}>{sym}</span>{' — '}{desc}</span>
          </div>
        ))}
      </div>)}
      {simData&&objLegend.length>0&&(<div style={{position:'absolute',top:14,right:14,
        background:'rgba(4,4,14,0.92)',border:'1px solid #1e1e2e',borderRadius:10,
        padding:'10px 14px',zIndex:15,pointerEvents:'none'}}>
        <div style={{color:'#444',fontSize:10,fontWeight:700,letterSpacing:'0.08em',marginBottom:7}}>OBJECTS</div>
        {objLegend.map((obj,i)=>(
          <div key={i} style={{display:'flex',alignItems:'center',gap:8,marginBottom:5}}>
            <div style={{width:10,height:10,borderRadius:'50%',background:obj.color||'#6366f1',flexShrink:0}}/>
            <span style={{color:'#ccc',fontSize:11,fontWeight:600}}>{obj.label||obj.id}</span>
          </div>
        ))}
      </div>)}
      {simData&&!loading&&(<div style={{position:'absolute',bottom:14,right:14,
        background:'rgba(5,5,15,0.75)',border:'1px solid #1e1e2e',borderRadius:8,
        padding:'7px 11px',color:'#444',fontSize:10,lineHeight:'1.8',pointerEvents:'none'}}>
        <div style={{color:'#666',fontWeight:700,marginBottom:3}}>CAMERA</div>
        <div>🖱 Drag — orbit &nbsp; ⚲ Scroll — zoom</div>
        <div><kbd style={KBD}>W</kbd><kbd style={KBD}>A</kbd><kbd style={KBD}>S</kbd><kbd style={KBD}>D</kbd> pan &nbsp;
          <kbd style={KBD}>Q</kbd><kbd style={KBD}>E</kbd> up/dn &nbsp;<kbd style={KBD}>R</kbd> reset view</div>
      </div>)}
    </div>
  );
});

const KBD={background:'#1a1a2a',border:'1px solid #2a2a3a',borderRadius:3,padding:'0 3px',margin:'0 1px',fontSize:9,color:'#888'};
function buildMesh(obj){
  const s=obj.size||0.5; let geometry,material;
  switch(obj.shape){
    case 'sphere':   geometry=new THREE.SphereGeometry(s,24,24); break;
    case 'box':      geometry=new THREE.BoxGeometry(s,s*(obj.height_ratio||1),s); break;
    case 'cylinder': geometry=new THREE.CylinderGeometry(s*0.25,s*0.25,s*3,16); break;
    case 'disk_3d':  geometry=new THREE.CylinderGeometry(obj.radius||s,obj.radius||s,0.12,32); break;
    case 'plane':    geometry=new THREE.PlaneGeometry(obj.width||20,obj.depth||20); break;
    case 'custom_incline':{
      const ang=(obj.angle_deg||30)*Math.PI/180,len=obj.length||8;
      const shape=new THREE.Shape([new THREE.Vector2(0,0),
        new THREE.Vector2(len*Math.cos(ang),len*Math.sin(ang)),new THREE.Vector2(len*Math.cos(ang),0)]);
      const m=new THREE.Mesh(new THREE.ShapeGeometry(shape),
        new THREE.MeshPhongMaterial({color:obj.color||'#2a2a3a',side:THREE.DoubleSide}));
      if(obj.position)m.position.set(...obj.position); return m;
    }
    default: geometry=new THREE.SphereGeometry(s,12,12);
  }
  material=new THREE.MeshPhongMaterial({color:obj.color||'#6366f1',shininess:80,
    transparent:obj.shape==='plane',opacity:obj.shape==='plane'?0.65:1,side:THREE.DoubleSide});
  const mesh=new THREE.Mesh(geometry,material);
  if(obj.position)mesh.position.set(...obj.position);
  if(obj.rotation)mesh.rotation.set(...obj.rotation);
  mesh.castShadow=true; return mesh;
}
function addAxes(scene){
  [[[1,0,0],'#ef444455'],[[0,1,0],'#22c55e55'],[[0,0,1],'#3b82f655']].forEach(([d,c])=>{
    scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(
      [new THREE.Vector3(0,0,0),new THREE.Vector3(...d).multiplyScalar(8)]),
      new THREE.LineBasicMaterial({color:c,transparent:true,opacity:0.25})));
  });
}
