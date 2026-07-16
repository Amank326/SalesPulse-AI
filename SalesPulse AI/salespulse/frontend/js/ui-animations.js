// Shared UI animation utilities for SalesPulse
// Provides initHeroCanvas() and initAuthBg() — safe no-op if canvas missing
(function(){
  function safeGet(id){ return document.getElementById(id); }

  window.initHeroCanvas = function initHeroCanvas(){
    const canvas = safeGet('heroCanvas');
    if (!canvas) return;
    if (window.__heroInitialized) return; window.__heroInitialized = true;
    const THREE = window.THREE;
    if (!THREE) return console.warn('Three.js not loaded');

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.position.z = 6;

    // particles
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 240;
    const pos = new Float32Array(particlesCount * 3);
    for (let i=0;i<particlesCount*3;i+=3){
      pos[i] = (Math.random()-0.5)*30;
      pos[i+1] = (Math.random()-0.5)*18;
      pos[i+2] = (Math.random()-0.5)*30;
    }
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(pos,3));
    const particlesMaterial = new THREE.PointsMaterial({ size: 0.08, vertexColors:false, color:0x00D9FF, transparent:true, opacity:0.85 });
    const particles = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particles);

    // floating mesh
    const boxGeo = new THREE.TorusKnotGeometry(0.9,0.25,128,16);
    const mat = new THREE.MeshStandardMaterial({ color: 0x7B3FF2, metalness:0.2, roughness:0.4, emissive:0x0 });
    const knot = new THREE.Mesh(boxGeo, mat);
    scene.add(knot);

    // lights
    const p1 = new THREE.PointLight(0x00D9FF, 1.2, 40);
    p1.position.set(6,4,8); scene.add(p1);
    const p2 = new THREE.PointLight(0x7B3FF2, 0.9, 40);
    p2.position.set(-6,-3,6); scene.add(p2);
    scene.add(new THREE.AmbientLight(0x888888, 0.6));

    let t = 0;
    function animate(){
      t += 0.01;
      knot.rotation.x += 0.006;
      knot.rotation.y += 0.01;
      knot.position.y = Math.sin(t) * 0.3;
      particles.rotation.y += 0.0008;
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    }
    animate();

    window.addEventListener('resize', ()=>{
      const w = window.innerWidth, h = window.innerHeight;
      camera.aspect = w/h; camera.updateProjectionMatrix(); renderer.setSize(w,h);
    });
  };

  window.initAuthBg = function initAuthBg(){
    const canvas = safeGet('authBgCanvas');
    if (!canvas) return;
    if (window.__authInitialized) return; window.__authInitialized = true;
    const THREE = window.THREE;
    if (!THREE) return console.warn('Three.js not loaded');

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.position.z = 5;

    const g = new THREE.BufferGeometry();
    const count = 160;
    const arr = new Float32Array(count*3);
    for (let i=0;i<count*3;i+=3){ arr[i] = (Math.random()-0.5)*22; arr[i+1] = (Math.random()-0.5)*12; arr[i+2] = (Math.random()-0.5)*22; }
    g.setAttribute('position', new THREE.BufferAttribute(arr,3));
    const material = new THREE.PointsMaterial({ size:0.06, color:0x7B3FF2, opacity:0.85 });
    const points = new THREE.Points(g, material); scene.add(points);

    const ambient = new THREE.AmbientLight(0x00D9FF, 0.2); scene.add(ambient);

    // Add large soft blobs (cloud-like spheres) for a richer Axlero-like background
    try { addAuthBlobs(scene); } catch(e) { /* ignore if fails */ }

    function anim(){
      points.rotation.y += 0.0005; renderer.render(scene, camera); requestAnimationFrame(anim);
    }
    anim();

    window.addEventListener('resize', ()=>{ const w = window.innerWidth, h = window.innerHeight; camera.aspect = w/h; camera.updateProjectionMatrix(); renderer.setSize(w,h); });
  };

  // Enhance auth background with soft gradient blobs to mimic Axlero hero
  // This will add two large, translucent spheres that slowly orbit
  function addAuthBlobs(scene){
    try {
      const THREE = window.THREE;
      const geo = new THREE.SphereGeometry(3.5, 64, 64);
      const matA = new THREE.MeshBasicMaterial({ color: 0x0044ff, transparent: true, opacity: 0.08, blending: THREE.AdditiveBlending });
      const matB = new THREE.MeshBasicMaterial({ color: 0x7B3FF2, transparent: true, opacity: 0.06, blending: THREE.AdditiveBlending });
      const a = new THREE.Mesh(geo, matA); a.position.set(-4,1,-6); a.scale.set(1.2,1.2,1.2);
      const b = new THREE.Mesh(geo, matB); b.position.set(4,-1,-6); b.scale.set(1.1,1.1,1.1);
      scene.add(a); scene.add(b);

      // store on window for animation loop integration
      if (!window.__authBlobs) window.__authBlobs = [];
      window.__authBlobs.push({mesh:a, speed:0.002, radius:0.4, baseY:a.position.y});
      window.__authBlobs.push({mesh:b, speed:0.0016, radius:0.55, baseY:b.position.y});
    } catch(e){/*ignore*/}
  }

  // Hook into existing loops: tweak initAuthBg and initHeroCanvas callers to animate blobs
  // We add a global animator tick that updates blobs if present
  (function globalBlobAnimator(){
    let gRunning = false;
    function tick(){
      if (window.__authBlobs && window.__authBlobs.length){
        const t = performance.now();
        window.__authBlobs.forEach((item,i)=>{
          item.mesh.rotation.y += 0.0006 + (i*0.0002);
          item.mesh.position.x += Math.sin(t*0.0001*item.speed) * 0.001;
          item.mesh.position.y = item.baseY + Math.sin(t*0.0005* (i+1) ) * item.radius;
        });
      }
      requestAnimationFrame(tick);
    }
    if (!gRunning){ gRunning = true; tick(); }
  })();
})();
