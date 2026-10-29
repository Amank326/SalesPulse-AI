// Advanced premium holographic 3D particle globe for SalesPulse AI
(function(){
  function safeGet(id){ return document.getElementById(id); }
  window.initHeroScene = function initHeroScene(){
    const canvas = safeGet('heroCanvas');
    if (!canvas) return;
    if (window.__heroSceneInit) return; window.__heroSceneInit = true;
    const THREE = window.THREE;
    if (!THREE) return console.warn('Three.js required for hero scene');

    // Renderer setting
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    function setSize(){ renderer.setSize(window.innerWidth, window.innerHeight); }
    setSize();
    
    const scene = new THREE.Scene();
    
    // Perspective Camera setup
    const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 0, 7.5);

    // ── LIGHTS ──
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambientLight);

    const primaryLight = new THREE.PointLight(0x00D9FF, 2, 20);
    primaryLight.position.set(4, 4, 4);
    scene.add(primaryLight);

    const accentLight = new THREE.PointLight(0x7B3FF2, 1.5, 20);
    accentLight.position.set(-4, -4, 4);
    scene.add(accentLight);

    // ── HOLOGRAPHIC GLOBE PARTICLES ──
    const globeRadius = 2.2;
    const globeGroup = new THREE.Group();
    scene.add(globeGroup);

    // Build particle points on a sphere
    const particleCount = 1200;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const colorPrimary = new THREE.Color(0x00D9FF);
    const colorSecondary = new THREE.Color(0x7B3FF2);

    for (let i = 0; i < particleCount; i++) {
      // Golden ratio placement for uniform sphere coverage
      const phi = Math.acos(-1 + (2 * i) / particleCount);
      const theta = Math.sqrt(particleCount * Math.PI) * phi;

      const x = globeRadius * Math.sin(phi) * Math.cos(theta);
      const y = globeRadius * Math.sin(phi) * Math.sin(theta);
      const z = globeRadius * Math.cos(phi);

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      // Color interpolation based on height/position
      const mixedColor = colorPrimary.clone().lerp(colorSecondary, (y + globeRadius) / (2 * globeRadius));
      colors[i * 3] = mixedColor.r;
      colors[i * 3 + 1] = mixedColor.g;
      colors[i * 3 + 2] = mixedColor.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // Glow points texture mapping
    const material = new THREE.PointsMaterial({
      size: 0.045,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    const globeParticles = new THREE.Points(geometry, material);
    globeGroup.add(globeParticles);

    // ── CONCENTRIC GLOWING DATA RINGS ──
    const ringGroup = new THREE.Group();
    globeGroup.add(ringGroup);

    const ringCount = 3;
    const ringRays = [];
    for (let i = 0; i < ringCount; i++) {
      const radius = globeRadius + 0.15 + (i * 0.2);
      const ringGeo = new THREE.RingGeometry(radius, radius + 0.015, 64);
      const ringMat = new THREE.MeshBasicMaterial({
        color: i % 2 === 0 ? 0x00D9FF : 0x7B3FF2,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.15 - (i * 0.04),
        blending: THREE.AdditiveBlending
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      
      // Pivot rotations slightly to look futuristic
      ring.rotation.x = Math.random() * Math.PI;
      ring.rotation.y = Math.random() * Math.PI;
      
      ringGroup.add(ring);
      ringRays.push({ mesh: ring, speedX: 0.002 * (i + 1), speedY: 0.001 * (i + 1) });
    }

    // ── DATA SHARDS (Floating crystals) ──
    const shardCount = 12;
    const shardGeo = new THREE.IcosahedronGeometry(0.15, 0);
    const shardMat = new THREE.MeshStandardMaterial({
      color: 0x38E2D8,
      metalness: 0.9,
      roughness: 0.1,
      transparent: true,
      opacity: 0.8,
      emissive: 0x003344
    });

    const shards = [];
    for (let i = 0; i < shardCount; i++) {
      const shardMesh = new THREE.Mesh(shardGeo, shardMat);
      
      // Random position in sphere shell surrounding the globe
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = globeRadius + 0.6 + Math.random() * 0.8;

      shardMesh.position.set(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi)
      );

      shardMesh.scale.setScalar(0.7 + Math.random() * 0.6);
      globeGroup.add(shardMesh);
      shards.push({
        mesh: shardMesh,
        speedX: (Math.random() - 0.5) * 0.01,
        speedY: (Math.random() - 0.5) * 0.01,
        orbitSpeed: 0.002 + Math.random() * 0.003,
        orbitRadius: r,
        angle: Math.random() * Math.PI * 2
      });
    }

    // ── BACKGROUND SPACE PARTICLES (Depth of field) ──
    const bgParticleCount = 350;
    const bgGeo = new THREE.BufferGeometry();
    const bgPositions = new Float32Array(bgParticleCount * 3);
    for (let i = 0; i < bgParticleCount; i++) {
      bgPositions[i * 3] = (Math.random() - 0.5) * 22;
      bgPositions[i * 3 + 1] = (Math.random() - 0.5) * 12;
      bgPositions[i * 3 + 2] = (Math.random() - 0.5) * 15 - 5; // pushed further back
    }
    bgGeo.setAttribute('position', new THREE.BufferAttribute(bgPositions, 3));
    const bgMat = new THREE.PointsMaterial({
      size: 0.05,
      color: 0x00D9FF,
      transparent: true,
      opacity: 0.35,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });
    const bgPoints = new THREE.Points(bgGeo, bgMat);
    scene.add(bgPoints);

    // ── MOUSE REACTIVE PARALLAX & LIGHTS ──
    const targetMouse = { x: 0, y: 0 };
    const currentMouse = { x: 0, y: 0 };

    window.addEventListener('mousemove', (ev) => {
      targetMouse.x = (ev.clientX / window.innerWidth) - 0.5;
      targetMouse.y = (ev.clientY / window.innerHeight) - 0.5;
    });

    // ── ANIMATION LOOP ──
    let time = 0;
    function animate() {
      time += 0.01;

      // Spin globe
      globeParticles.rotation.y += 0.0025;
      globeParticles.rotation.x = Math.sin(time * 0.2) * 0.05;

      // Animate Concentric Rings
      ringRays.forEach(item => {
        item.mesh.rotation.x += item.speedX;
        item.mesh.rotation.y += item.speedY;
      });

      // Animate Shards
      shards.forEach(s => {
        s.mesh.rotation.x += s.speedX;
        s.mesh.rotation.y += s.speedY;
        
        // Orbit around Y axis
        s.angle += s.orbitSpeed;
        s.mesh.position.x = Math.cos(s.angle) * s.orbitRadius;
        s.mesh.position.z = Math.sin(s.angle) * s.orbitRadius;
      });

      // Slowly rotate background stars
      bgPoints.rotation.y += 0.0003;
      bgPoints.rotation.x += 0.0001;

      // Smooth interpolation for mouse movements
      currentMouse.x += (targetMouse.x - currentMouse.x) * 0.05;
      currentMouse.y += (targetMouse.y - currentMouse.y) * 0.05;

      // Parallax camera movement
      camera.position.x = currentMouse.x * 1.8;
      camera.position.y = -currentMouse.y * 1.8;
      camera.lookAt(0, 0, 0);

      // Mouse reactive lighting tracking
      primaryLight.position.x = 4 + currentMouse.x * 8;
      primaryLight.position.y = 4 - currentMouse.y * 8;

      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    }
    animate();

    // Responsive camera aspect ratio adjustment
    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      setSize();
    });
  };

  // Auto-init on page load
  window.addEventListener('DOMContentLoaded', () => {
    try {
      if (document.getElementById('heroCanvas') && window.initHeroScene) {
        window.initHeroScene();
      }
    } catch(e) {}
  });
})();
