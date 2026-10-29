// Premium fluid particle space for SalesPulse AI Authentication Pages
(function(){
  function safeGet(id){ return document.getElementById(id); }

  window.initAuthBg = function initAuthBg(){
    const canvas = safeGet('authBgCanvas');
    if (!canvas) return;
    if (window.__authInitialized) return; window.__authInitialized = true;
    const THREE = window.THREE;
    if (!THREE) return console.warn('Three.js not loaded');

    const scene = new THREE.Scene();
    
    // Camera setting
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 0, 5);

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);

    // ── LIGHTS ──
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
    scene.add(ambientLight);

    const pLight1 = new THREE.PointLight(0x00D9FF, 1.5, 15);
    pLight1.position.set(3, 3, 3);
    scene.add(pLight1);

    const pLight2 = new THREE.PointLight(0x7B3FF2, 1.2, 15);
    pLight2.position.set(-3, -3, 3);
    scene.add(pLight2);

    // ── FLUID PARTICLE STREAM ──
    const count = 300;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const originalY = new Float32Array(count);
    const speeds = new Float32Array(count);
    const waveFreq = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      // Flow particles from left to right with sine waves
      positions[i * 3] = (Math.random() - 0.5) * 12;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 6;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 6;

      originalY[i] = positions[i * 3 + 1];
      speeds[i] = 0.005 + Math.random() * 0.015;
      waveFreq[i] = 0.5 + Math.random() * 1.5;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      size: 0.05,
      color: 0x7B3FF2,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    // ── GLOWING AURORA SPHERES (Post-processing blur simulation) ──
    const blobGeo = new THREE.SphereGeometry(2.5, 32, 32);
    const blobMat1 = new THREE.MeshBasicMaterial({
      color: 0x0044ff,
      transparent: true,
      opacity: 0.06,
      blending: THREE.AdditiveBlending
    });
    const blobMat2 = new THREE.MeshBasicMaterial({
      color: 0x7B3FF2,
      transparent: true,
      opacity: 0.05,
      blending: THREE.AdditiveBlending
    });

    const blob1 = new THREE.Mesh(blobGeo, blobMat1);
    blob1.position.set(-3, 1, -4);
    
    const blob2 = new THREE.Mesh(blobGeo, blobMat2);
    blob2.position.set(3, -1, -4);

    scene.add(blob1);
    scene.add(blob2);

    // ── INTERACTIVE MOUSE PARALLAX ──
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    window.addEventListener('mousemove', (e) => {
      mouse.targetX = (e.clientX / window.innerWidth) - 0.5;
      mouse.targetY = (e.clientY / window.innerHeight) - 0.5;
    });

    // ── ANIMATION TICK ──
    let time = 0;
    function anim(){
      time += 0.01;

      // Update particle positions (flow wave logic)
      const posAttr = geometry.attributes.position;
      for (let i = 0; i < count; i++) {
        const i3 = i * 3;
        // Flow horizontally
        posAttr.array[i3] += speeds[i];
        // Sine wave fluctuation
        posAttr.array[i3 + 1] = originalY[i] + Math.sin(time * waveFreq[i] + posAttr.array[i3]) * 0.35;

        // Wrap around boundary
        if (posAttr.array[i3] > 6) {
          posAttr.array[i3] = -6;
        }
      }
      posAttr.needsUpdate = true;

      // Slowly rotate and float the background blobs
      blob1.position.x = -3 + Math.sin(time * 0.2) * 0.5;
      blob1.position.y = 1 + Math.cos(time * 0.2) * 0.3;
      blob2.position.x = 3 + Math.cos(time * 0.15) * 0.5;
      blob2.position.y = -1 + Math.sin(time * 0.15) * 0.3;

      // Mouse Parallax camera glide
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;
      camera.position.x = mouse.x * 1.5;
      camera.position.y = -mouse.y * 1.5;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
      requestAnimationFrame(anim);
    }
    anim();

    // Resize handler
    window.addEventListener('resize', ()=>{
      const w = window.innerWidth, h = window.innerHeight;
      camera.aspect = w/h;
      camera.updateProjectionMatrix();
      renderer.setSize(w,h);
    });
  };
})();
