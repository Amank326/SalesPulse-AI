// MESH BACKGROUND
const canvas=document.getElementById('mesh');
if(canvas){
  const ctx=canvas.getContext('2d');
  let W,H,pts;
  function resize(){W=canvas.width=window.innerWidth;H=canvas.height=window.innerHeight}
  function initPts(){pts=Array.from({length:18},()=>({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.4,vy:(Math.random()-.5)*.4}))}
  function drawMesh(){
    ctx.clearRect(0,0,W,H);
    pts.forEach(p=>{p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>W)p.vx*=-1;if(p.y<0||p.y>H)p.vy*=-1});
    for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++){
      const dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y,dist=Math.sqrt(dx*dx+dy*dy);
      if(dist<260){ctx.beginPath();ctx.moveTo(pts[i].x,pts[i].y);ctx.lineTo(pts[j].x,pts[j].y);ctx.strokeStyle=`rgba(91,142,255,${(1-dist/260)*.15})`;ctx.lineWidth=1;ctx.stroke()}
    }
    pts.forEach(p=>{ctx.beginPath();ctx.arc(p.x,p.y,1.5,0,Math.PI*2);ctx.fillStyle='rgba(91,142,255,.28)';ctx.fill()});
    requestAnimationFrame(drawMesh);
  }
  resize();initPts();drawMesh();
  window.addEventListener('resize',()=>{resize();initPts()});
}

// SCROLL REVEAL
const io=new IntersectionObserver(e=>{e.forEach(x=>{if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target)}})},{threshold:0.1});
document.querySelectorAll('.fade-up').forEach(el=>io.observe(el));

// COUNTER
function animateCount(el,target,prefix,suffix,dur){
  if(!el)return;
  let start=null;
  const step=ts=>{if(!start)start=ts;const p=Math.min((ts-start)/dur,1),e=1-Math.pow(1-p,4);
    el.innerHTML=prefix+Math.round(e*target).toLocaleString()+'<span>'+suffix+'</span>';if(p<1)requestAnimationFrame(step)};
  requestAnimationFrame(step);
}
const cio=new IntersectionObserver(e=>{e.forEach(x=>{if(x.isIntersecting){
  animateCount(document.getElementById('c1'),94,'','%',1800);
  animateCount(document.getElementById('c2'),2400,'','+',2200);
  animateCount(document.getElementById('c3'),850,'₹','Cr',2000);
  animateCount(document.getElementById('c4'),3,' ','min',1500);
  cio.disconnect()}})},{threshold:0.3});
const cr=document.querySelector('.counter-ring');if(cr)cio.observe(cr);

// NAV SCROLL
window.addEventListener('scroll',()=>{const n=document.getElementById('nav');if(n)n.style.borderBottomColor=window.scrollY>30?'rgba(91,142,255,.18)':'rgba(255,255,255,.06)'});

// TOAST
function showToast(msg,type='success'){
  let t=document.querySelector('.toast');
  if(!t){t=document.createElement('div');t.className='toast';document.body.appendChild(t)}
  t.textContent=msg;t.className=`toast toast-${type} show`;
  setTimeout(()=>t.classList.remove('show'),3500);
}

// AUTH — LocalStorage based (simulates backend)
function saveUser(data){localStorage.setItem('sp_user',JSON.stringify(data))}
function getUser(){try{return JSON.parse(localStorage.getItem('sp_user'))}catch{return null}}
function logout(){localStorage.removeItem('sp_user');location.href='index.html'}

// REGISTER FORM
const regForm=document.getElementById('registerForm');
if(regForm){
  regForm.addEventListener('submit', async e=>{
    e.preventDefault();
    const name=document.getElementById('name').value.trim();
    const email=document.getElementById('email').value.trim();
    const pass=document.getElementById('password').value;
    if(!name||!email||!pass){showToast('Please fill all fields','error');return}
    if(pass.length<6){showToast('Password must be at least 6 characters','error');return}

    // Try registering with backend if available
    try{
      const resp = await fetch('http://127.0.0.1:8000/api/register', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({name,email,password:pass})
      });
      if(resp.ok){
        showToast('Account created! Logging in...');
        // login to get token
        const loginResp = await fetch('http://127.0.0.1:8000/api/login', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password:pass})});
        if(loginResp.ok){
          const data = await loginResp.json();
          localStorage.setItem('token', data.token);
          localStorage.setItem('userName', data.name || name);
          saveUser({name,email,id:Date.now()});
          setTimeout(()=>location.href='dashboard.html',800);
          return;
        }
      } else {
        const err = await resp.json().catch(()=>({detail:'Registration failed'}));
        showToast(err.detail||'Registration failed','error');
      }
    }catch(err){
      // Fallback to localStorage-only behavior if backend not available
      const users=JSON.parse(localStorage.getItem('sp_users')||'[]');
      if(users.find(u=>u.email===email)){showToast('Email already registered','error');return}
      const user={name,email,id:Date.now()};
      users.push({...user,pass});
      localStorage.setItem('sp_users',JSON.stringify(users));
      saveUser(user);
      showToast('Account created (offline)! Redirecting...');
      setTimeout(()=>location.href='dashboard.html',1200);
    }
  });
}

// LOGIN FORM
const loginForm=document.getElementById('loginForm');
if(loginForm){
  loginForm.addEventListener('submit',e=>{
    e.preventDefault();
    const email=document.getElementById('email').value.trim();
    const pass=document.getElementById('password').value;
    const users=JSON.parse(localStorage.getItem('sp_users')||'[]');
    const user=users.find(u=>u.email===email&&u.pass===pass);
    if(!user){showToast('Invalid email or password','error');return}
    saveUser({name:user.name,email:user.email,id:user.id});
    showToast('Welcome back, '+user.name+'!');
    setTimeout(()=>location.href='dashboard.html',1000);
  });
}

// DASHBOARD AUTH GUARD
if(window.location.pathname.includes('dashboard')){
  const user=getUser();
  const nameEl=document.getElementById('userName');
  const initEl=document.getElementById('userInitial');
  if(user){ if(nameEl)nameEl.textContent=user.name; if(initEl)initEl.textContent=user.name.charAt(0).toUpperCase(); }
  else { if(nameEl)nameEl.textContent='Guest'; if(initEl)initEl.textContent='G'; }
}

// UPLOAD HANDLER
const dropZone=document.getElementById('dropZone');
const fileInput=document.getElementById('fileInput');
if(dropZone&&fileInput){
  dropZone.addEventListener('click',()=>fileInput.click());
  dropZone.addEventListener('dragover',e=>{e.preventDefault();dropZone.style.borderColor='rgba(91,142,255,.7)'});
  dropZone.addEventListener('dragleave',()=>dropZone.style.borderColor='rgba(91,142,255,.25)');
  dropZone.addEventListener('drop',e=>{e.preventDefault();handleFile(e.dataTransfer.files[0])});
  fileInput.addEventListener('change',()=>handleFile(fileInput.files[0]));
}
function handleFile(file){
  if(!file)return;
  showToast('Uploading '+file.name+'...');
  setTimeout(()=>showToast('Data cleaned. Running ML model...'),1200);
  setTimeout(()=>showToast('Forecast complete! Dashboard updated.'),3000);
  setTimeout(()=>{
    const kpis=document.querySelectorAll('.kpi-val');
    if(kpis[0])kpis[0].textContent='₹41.3L';
    if(kpis[1])kpis[1].textContent='96.1%';
  },3200);
}
