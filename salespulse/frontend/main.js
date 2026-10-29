// ═══════════════════════════════════════════════════════════════════════════
// SalesPulse AI — Shared Premium JS Logic
// Includes GSAP Magnetic Buttons, Transitions, and Core Actions
// ═══════════════════════════════════════════════════════════════════════════

// ── API CONFIGURATION ──
// Use the local API during development and the public API when hosted.
const isLocalHost = ['localhost', '127.0.0.1'].includes(window.location.hostname);
window.API_BASE = window.API_BASE || (
  isLocalHost ? 'http://127.0.0.1:8000' : 'https://salespulse-ai-api.onrender.com'
);

// ── GSAP MAGNETIC BUTTON EFFECT ──
function initMagneticButtons() {
  const GSAP = window.gsap;
  if (!GSAP) return;

  document.querySelectorAll('.magnetic-btn').forEach(btn => {
    btn.addEventListener('mousemove', (e) => {
      const bound = btn.getBoundingClientRect();
      // Calculate cursor position relative to button center
      const x = e.clientX - bound.left - bound.width / 2;
      const y = e.clientY - bound.top - bound.height / 2;
      
      GSAP.to(btn, {
        x: x * 0.35,
        y: y * 0.35,
        duration: 0.3,
        ease: "power2.out"
      });
    });
    
    btn.addEventListener('mouseleave', () => {
      GSAP.to(btn, {
        x: 0,
        y: 0,
        duration: 0.6,
        ease: "elastic.out(1, 0.3)"
      });
    });
  });
}

// ── PAGE ENTRANCE TRANSITIONS ──
function initPageTransitions() {
  const GSAP = window.gsap;
  if (!GSAP) return;

  // Animate main container on load
  const mainContent = document.querySelector('.dash-main') || document.querySelector('.auth-container') || document.querySelector('.hero-content');
  if (mainContent) {
    GSAP.fromTo(mainContent, 
      { opacity: 0, y: 15 },
      { opacity: 1, y: 0, duration: 0.8, ease: "power4.out" }
    );
  }

  // Intercept links to play transition
  document.querySelectorAll('a').forEach(link => {
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;
    
    link.addEventListener('click', (e) => {
      e.preventDefault();
      if (mainContent) {
        GSAP.to(mainContent, {
          opacity: 0,
          y: -15,
          duration: 0.4,
          ease: "power4.in",
          onComplete: () => {
            window.location.href = href;
          }
        });
      } else {
        window.location.href = href;
      }
    });
  });
}

// ── MESH CANVAS BACKGROUND ──
const canvas = document.getElementById('mesh');
if (canvas) {
  const ctx = canvas.getContext('2d');
  let W, H, pts;
  function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
  function initPts() {
    pts = Array.from({ length: 18 }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4
    }));
  }
  function drawMesh() {
    ctx.clearRect(0, 0, W, H);
    pts.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > W) p.vx *= -1;
      if (p.y < 0 || p.y > H) p.vy *= -1;
    });
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 260) {
          ctx.beginPath();
          ctx.moveTo(pts[i].x, pts[i].y);
          ctx.lineTo(pts[j].x, pts[j].y);
          ctx.strokeStyle = `rgba(91,142,255,${(1 - dist / 260) * 0.15})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }
    pts.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(91,142,255,.28)';
      ctx.fill();
    });
    requestAnimationFrame(drawMesh);
  }
  resize(); initPts(); drawMesh();
  window.addEventListener('resize', () => { resize(); initPts(); });
}

// ── SCROLL REVEAL OBSERVER ──
const io = new IntersectionObserver(e => {
  e.forEach(x => {
    if (x.isIntersecting) { x.target.classList.add('in'); io.unobserve(x.target); }
  });
}, { threshold: 0.1 });
document.querySelectorAll('.fade-up').forEach(el => io.observe(el));

// ── COUNTER ANIMATIONS ──
function animateCount(el, target, prefix, suffix, dur) {
  if (!el) return;
  let start = null;
  const step = ts => {
    if (!start) start = ts;
    const p = Math.min((ts - start) / dur, 1);
    const e = 1 - Math.pow(1 - p, 4);
    el.innerHTML = prefix + Math.round(e * target).toLocaleString() + '<span>' + suffix + '</span>';
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
const cio = new IntersectionObserver(e => {
  e.forEach(x => {
    if (x.isIntersecting) {
      animateCount(document.getElementById('c1'), 94, '', '%', 1800);
      animateCount(document.getElementById('c2'), 2400, '', '+', 2200);
      animateCount(document.getElementById('c3'), 850, '₹', 'Cr', 2000);
      animateCount(document.getElementById('c4'), 3, ' ', 'min', 1500);
      cio.disconnect();
    }
  });
}, { threshold: 0.3 });
const cr = document.querySelector('.counter-ring');
if (cr) cio.observe(cr);

// ── NAV BAR SCROLL EFFECT ──
window.addEventListener('scroll', () => {
  const n = document.getElementById('nav');
  if (n) n.style.borderBottomColor = window.scrollY > 30 ? 'rgba(255,255,255,.09)' : 'rgba(255,255,255,.05)';
});

// ── TOAST MESSAGES ──
function showToast(msg, type = 'success') {
  let t = document.querySelector('.toast');
  if (!t) {
    t = document.createElement('div');
    t.className = 'toast';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.className = 'toast toast-' + type + ' show';
  setTimeout(() => t.classList.remove('show'), 3500);
}

// ── AUTH ACCESS ──
function saveUser(data) { localStorage.setItem('sp_user', JSON.stringify(data)); }
function getUser() { try { return JSON.parse(localStorage.getItem('sp_user')); } catch { return null; } }
function logout() {
  localStorage.removeItem('sp_user');
  localStorage.removeItem('token');
  localStorage.removeItem('userName');
  location.href = 'index.html';
}

// ── REGISTER FORM POST ──
const regForm = document.getElementById('registerForm');
if (regForm) {
  regForm.addEventListener('submit', async e => {
    e.preventDefault();
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const pass = document.getElementById('password').value;
    if (!name || !email || !pass) { showToast('Please fill all fields', 'error'); return; }
    if (pass.length < 6) { showToast('Password must be at least 6 characters', 'error'); return; }

    try {
      const resp = await fetch(window.API_BASE + '/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password: pass })
      });
      if (resp.ok) {
        const data = await resp.json();
        localStorage.setItem('token', data.token);
        localStorage.setItem('userName', data.name || name);
        saveUser({ name: data.name || name, email: data.email || email, id: Date.now() });
        showToast('Account created! Redirecting...');
        setTimeout(() => location.href = 'dashboard.html', 800);
      } else {
        const err = await resp.json().catch(() => ({ detail: 'Registration failed' }));
        showToast(err.detail || 'Registration failed', 'error');
      }
    } catch (err) {
      const users = JSON.parse(localStorage.getItem('sp_users') || '[]');
      if (users.find(u => u.email === email)) { showToast('Email already registered', 'error'); return; }
      const user = { name, email, id: Date.now() };
      users.push({ ...user, pass });
      localStorage.setItem('sp_users', JSON.stringify(users));
      saveUser(user);
      showToast('Account created (offline)! Redirecting...');
      setTimeout(() => location.href = 'dashboard.html', 1200);
    }
  });
}

// ── LOGIN FORM POST ──
const loginForm = document.getElementById('loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    const email = document.getElementById('email').value.trim();
    const pass = document.getElementById('password').value;
    if (!email || !pass) { showToast('Please fill all fields', 'error'); return; }

    try {
      const resp = await fetch(window.API_BASE + '/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: pass })
      });
      if (resp.ok) {
        const data = await resp.json();
        localStorage.setItem('token', data.token);
        localStorage.setItem('userName', data.name || email);
        saveUser({ name: data.name, email: data.email, id: Date.now() });
        showToast('Welcome back, ' + (data.name || email) + '!');
        setTimeout(() => location.href = 'dashboard.html', 800);
      } else {
        const err = await resp.json().catch(() => ({ detail: 'Invalid credentials' }));
        showToast(err.detail || 'Invalid email or password', 'error');
      }
    } catch (err) {
      const users = JSON.parse(localStorage.getItem('sp_users') || '[]');
      const user = users.find(u => u.email === email && u.pass === pass);
      if (!user) { showToast('Invalid email or password', 'error'); return; }
      saveUser({ name: user.name, email: user.email, id: user.id });
      showToast('Welcome back, ' + user.name + '! (offline)');
      setTimeout(() => location.href = 'dashboard.html', 1000);
    }
  });
}

// ── DASHBOARD AUTH GUARD ──
if (window.location.pathname.includes('dashboard') || window.location.pathname.includes('upload') || window.location.pathname.includes('forecast')) {
  const user = getUser();
  const nameEl = document.getElementById('userName');
  const initEl = document.getElementById('userInitial');
  if (user) {
    if (nameEl) nameEl.textContent = user.name;
    if (initEl) initEl.textContent = user.name.charAt(0).toUpperCase();
  }
}

// ── INITIALIZE EFFECTS ──
window.addEventListener('DOMContentLoaded', () => {
  initMagneticButtons();
  initPageTransitions();
});
