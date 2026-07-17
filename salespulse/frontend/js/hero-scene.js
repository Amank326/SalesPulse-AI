// Enhanced hero 3D scene for SalesPulse — procedural crystals, particles, parallax
(function(){
  function safeGet(id){ return document.getElementById(id); }
  window.initHeroScene = function initHeroScene(){
    const canvas = safeGet('heroCanvas');
    if (!canvas) return;
    if (window.__heroSceneInit) return; window.__heroSceneInit = true;
    const THREE = window.THREE;
    if (!THREE) return console.warn('Three.js required for hero scene');

    // renderer & basic scene
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    function setSize(){ renderer.setSize(window.innerWidth, window.innerHeight); }
    setSize();
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth/window.innerHeight, 0.1, 1000);
    camera.position.set(0, 0, 6);

    // Lighting
    const ambient = new THREE.AmbientLight(0xffffff, 0.35); scene.add(ambient);
    const rim = new THREE.DirectionalLight(0x9be7ff, 0.8); rim.position.set(-4,3,6); scene.add(rim);
    const fill = new THREE.PointLight(0xff8edf, 0.6, 30); fill.position.set(4,-2,3); scene.add(fill);

    // central crystal (icosahedron with vertex wobble)
    const icoGeo = new THREE.IcosahedronGeometry(1.2, 2);
    // backup original positions for wobble
    const origPos = new Float32Array(icoGeo.attributes.position.array.length);
    origPos.set(icoGeo.attributes.position.array);
    icoGeo.setAttribute('origPos', new THREE.BufferAttribute(origPos, 3));
    const crystalMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      metalness: 0.25,
      roughness: 0.05,
      emissive: 0x4b2fff,
      emissiveIntensity: 0.15,
      transparent: true,
      opacity: 0.98,
      envMapIntensity: 0.6
    });
    const crystal = new THREE.Mesh(icoGeo, crystalMat); crystal.castShadow = true; scene.add(crystal);

    // ring of shards
    const shards = new THREE.Group();
    const shardGeo = new THREE.OctahedronGeometry(0.28,0);
    const shardMat = new THREE.MeshStandardMaterial({ color:0x7B3FF2, metalness:0.18, roughness:0.2, emissive:0x001122, transparent:true, opacity:0.92});
    for(let i=0;i<18;i++){
      const m = new THREE.Mesh(shardGeo, shardMat);
      const a = (i/18)*Math.PI*2;
      const r = 2.2 + Math.random()*0.35;
      m.position.set(Math.cos(a)*r, (Math.random()-0.5)*0.5, Math.sin(a)*r);
      m.lookAt(0,0,0);
      m.scale.setScalar(0.9+Math.random()*0.5);
      shards.add(m);
    }
    scene.add(shards);

    // soft particle field for depth
    const particleCount = 400;
    const pg = new THREE.BufferGeometry();
    const pArr = new Float32Array(particleCount*3);
    for(let i=0;i<particleCount;i++){
      pArr[i*3] = (Math.random()-0.5)*20;
      pArr[i*3+1] = (Math.random()-0.5)*10;
      pArr[i*3+2] = (Math.random()-0.5)*20;
    }
    pg.setAttribute('position', new THREE.BufferAttribute(pArr,3));
    const pm = new THREE.PointsMaterial({ size:0.06, color:0x9be7ff, transparent:true, opacity:0.65, depthWrite:false });
    const particles = new THREE.Points(pg, pm); scene.add(particles);

    // subtle CSS card parallax (floating cards in hero)
    const cards = document.querySelectorAll('.floating-cards .card');

    // mouse parallax
    const state = { mx:0, my:0, tx:0, ty:0 };
    window.addEventListener('mousemove', (ev)=>{
      const nx = (ev.clientX/window.innerWidth)-0.5;
      const ny = (ev.clientY/window.innerHeight)-0.5;
      state.mx = nx; state.my = ny;
    });

    // animate loop
    let time = 0;
    function animate(){
      time += 0.01;
      // wobble crystal vertices
      const posAttr = icoGeo.attributes.position;
      const orig = icoGeo.attributes.origPos.array;
      for(let i=0;i<posAttr.count;i++){
        const ix = i*3, iy = ix+1, iz = ix+2;
        posAttr.array[ix] = orig[ix] + Math.sin(time*2 + i)*0.02;
        posAttr.array[iy] = orig[iy] + Math.cos(time*1.5 + i*0.3)*0.02;
        posAttr.array[iz] = orig[iz] + Math.sin(time*1.2 + i*0.7)*0.01;
      }
      posAttr.needsUpdate = true;

      crystal.rotation.y += 0.005;
      crystal.rotation.x = Math.sin(time*0.3)*0.08;

      shards.rotation.y -= 0.002;
      shards.children.forEach((c,i)=>{ c.rotation.z += 0.002 + (i*0.0001); });

      particles.rotation.y += 0.0006;

      // smooth camera follow mouse
      state.tx += (state.mx*1.8 - state.tx) * 0.06;
      state.ty += (state.my*0.6 - state.ty) * 0.06;
      camera.position.x = state.tx * 1.4;
      camera.position.y = -state.ty * 1.2;
      camera.lookAt(0,0,0);

      // card CSS parallax
      cards.forEach((el,idx)=>{
        const depth = (idx - (cards.length/2)) * 6;
        const rx = state.mx * 10 * (0.6 + idx*0.08);
        const ry = state.my * 8 * (0.6 + idx*0.06);
        el.style.transform = `translate3d(${rx}px, ${-ry}px, 0) rotate(${rx*0.02}deg)`;
      });

      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    }
    animate();

    window.addEventListener('resize', ()=>{ camera.aspect = window.innerWidth/window.innerHeight; camera.updateProjectionMatrix(); setSize(); });
  };
  // auto-init on DOMContentLoaded if hero present (keeps existing workflows simple)
  window.addEventListener('DOMContentLoaded', ()=>{ try{ if (document.getElementById('heroCanvas') && window.initHeroScene) initHeroScene(); }catch(e){} });
})();
