/* ============================================================
   CRISIS-X AI — Shared API Client & Auth Guard
   Include this script on every page: <script src="api.js"></script>
   ============================================================ */

const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? `http://${window.location.hostname}:5000`
  : '';  // same origin in production

/* ── Token helpers ─────────────────────────────────────────── */
const Auth = {
  getToken: ()  => localStorage.getItem('crisisx_token'),
  setToken: (t) => localStorage.setItem('crisisx_token', t),
  getUser:  ()  => { try { return JSON.parse(localStorage.getItem('crisisx_user') || 'null'); } catch { return null; } },
  setUser:  (u) => localStorage.setItem('crisisx_user', JSON.stringify(u)),
  clear:    ()  => { localStorage.removeItem('crisisx_token'); localStorage.removeItem('crisisx_user'); },
  isLoggedIn: () => !!localStorage.getItem('crisisx_token'),
};

/* ── Core fetch wrapper ────────────────────────────────────── */
async function apiRequest(path, options = {}) {
  const token = Auth.getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(API_BASE + path, { ...options, headers });

  if (res.status === 401) {
    Auth.clear();
    redirectToLogin();
    return null;
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

/* ── Auth guard — call on every protected page ─────────────── */
async function requireAuth() {
  if (!Auth.isLoggedIn()) { redirectToLogin(); return null; }
  try {
    const user = await apiRequest('/api/auth/me');
    if (!user) return null;
    Auth.setUser(user);
    return user;
  } catch {
    Auth.clear();
    redirectToLogin();
    return null;
  }
}

function redirectToLogin() {
  const here = encodeURIComponent(window.location.pathname + window.location.search);
  window.location.href = `login.html?redirect=${here}`;
}

/* ── Logout ────────────────────────────────────────────────── */
function logout() {
  Auth.clear();
  window.location.href = 'login.html';
}

/* ── API helpers ───────────────────────────────────────────── */
const CrisisAPI = {
  login:          (email, password) => apiRequest('/api/auth/login', { method:'POST', body: JSON.stringify({email,password}) }),
  signup:         (name, email, password) => apiRequest('/api/auth/signup', { method:'POST', body: JSON.stringify({name,email,password}) }),
  me:             () => apiRequest('/api/auth/me'),
  globalRisk:     () => apiRequest('/api/risk/global'),
  countries:      () => apiRequest('/api/risk/countries'),
  topCountries:   (n) => apiRequest(`/api/risk/countries/top/${n}`),
  marketIndicators: () => apiRequest('/api/markets/indicators'),
  vixHistory:     (range) => apiRequest(`/api/markets/vix/${range}`),
  alerts:         () => apiRequest('/api/alerts'),
  alert:          (id) => apiRequest(`/api/alerts/${id}`),
  banks:          () => apiRequest('/api/banks'),
  news:           () => apiRequest('/api/news'),
  newsSentiment:  () => apiRequest('/api/news/sentiment'),
  crisisList:     () => apiRequest('/api/crisis'),
  crisisDetail:   (year) => apiRequest(`/api/crisis/${year}`),
  stats:          () => apiRequest('/api/stats'),
  chat:           (message) => apiRequest('/api/chat', { method:'POST', body: JSON.stringify({message}) }),
  chatHistory:    () => apiRequest('/api/chat/history'),
};

/* ── Populate user info in nav (if elements exist) ─────────── */
function populateUserNav(user) {
  const nameEls = document.querySelectorAll('[data-user-name]');
  const emailEls = document.querySelectorAll('[data-user-email]');
  const roleEls  = document.querySelectorAll('[data-user-role]');
  const avatarEls = document.querySelectorAll('[data-user-avatar]');
  nameEls.forEach(el => el.textContent = user.name || 'User');
  emailEls.forEach(el => el.textContent = user.email || '');
  roleEls.forEach(el => el.textContent = user.role || 'user');
  avatarEls.forEach(el => el.textContent = (user.name || 'U')[0].toUpperCase());
}
