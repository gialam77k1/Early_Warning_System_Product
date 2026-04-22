/**
 * Early Warning System — API Utility
 * Xử lý JWT auth + tất cả API calls đến Django backend
 */

const API_BASE = '/api';

const api = {
  /* ── Headers ── */
  getHeaders() {
    const token = localStorage.getItem('ews_access');
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  },

  /* ── Core request ── */
  async request(method, endpoint, data = null) {
    const options = { method, headers: this.getHeaders() };
    if (data) options.body = JSON.stringify(data);

    let resp = await fetch(`${API_BASE}${endpoint}`, options);

    // 401 → thử refresh token
    if (resp.status === 401) {
      const ok = await this.refreshToken();
      if (ok) {
        options.headers = this.getHeaders();
        resp = await fetch(`${API_BASE}${endpoint}`, options);
      } else {
        this.logout();
        return null;
      }
    }
    return resp;
  },

  /* ── Token refresh ── */
  async refreshToken() {
    const refresh = localStorage.getItem('ews_refresh');
    if (!refresh) return false;
    const resp = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (resp.ok) {
      const data = await resp.json();
      localStorage.setItem('ews_access', data.access);
      return true;
    }
    return false;
  },

  /* ── Shortcuts ── */
  async get(endpoint)         { return this.request('GET',    endpoint); },
  async post(endpoint, data)  { return this.request('POST',   endpoint, data); },
  async put(endpoint, data)   { return this.request('PUT',    endpoint, data); },
  async patch(endpoint, data) { return this.request('PATCH',  endpoint, data); },
  async del(endpoint)         { return this.request('DELETE', endpoint); },

  /* ── Auth helpers ── */
  getUser()    { try { return JSON.parse(localStorage.getItem('ews_user')); } catch { return null; } },
  isLoggedIn() { return !!localStorage.getItem('ews_access'); },

  async login(username, password) {
    const resp = await fetch(`${API_BASE}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (resp.ok) {
      const data = await resp.json();
      localStorage.setItem('ews_access',  data.access);
      localStorage.setItem('ews_refresh', data.refresh);
      localStorage.setItem('ews_user',    JSON.stringify(data.user));
      return { ok: true, user: data.user };
    }
    const err = await resp.json();
    const msg = err.non_field_errors?.[0] || err.detail || 'Đăng nhập thất bại';
    return { ok: false, msg };
  },

  logout() {
    // Gọi API logout (blacklist token) nếu có thể
    const refresh = localStorage.getItem('ews_refresh');
    if (refresh) {
      fetch(`${API_BASE}/auth/logout/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ refresh }),
      }).catch(() => {});
    }
    localStorage.removeItem('ews_access');
    localStorage.removeItem('ews_refresh');
    localStorage.removeItem('ews_user');
    window.location.href = getLoginUrl();
  },
};

/* ── Utility ── */
function getLoginUrl() {
  // Xác định đường dẫn login từ bất kỳ trang nào
  const path = window.location.pathname;
  const depth = (path.match(/\//g) || []).length - 1;
  return depth > 1 ? '../index.html' : 'index.html';
}

function requireAuth(allowedRoles = []) {
  if (!api.isLoggedIn()) {
    window.location.href = getLoginUrl();
    return null;
  }
  const user = api.getUser();
  if (allowedRoles.length && !allowedRoles.includes(user?.vai_tro)) {
    alert('Bạn không có quyền truy cập trang này.');
    window.location.href = getLoginUrl();
    return null;
  }
  return user;
}

function showToast(msg, type = 'success') {
  const existing = document.getElementById('ews-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'ews-toast';
  toast.className = `toast toast-${type}`;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.classList.add('show'), 10);
  setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 3000);
}

function getRiskBadge(level) {
  const map = {
    high_risk:   ['At Risk',    'badge-red'],
    medium_risk: ['Average',     'badge-orange'],
    low_risk:    ['Good',       'badge-blue'],
    no_risk:     ['Excellent',  'badge-green'],
  };
  const [txt, cls] = map[level] || [level, 'badge-secondary'];
  return `<span class="badge ${cls}">${txt}</span>`;
}

function getLabelBadge(label) {
  const map = {
    Excellent: ['badge-excellent', 'Excellent'],
    Good:      ['badge-green',     'Good'],
    Average:   ['badge-blue',      'Average'],
    Weak:      ['badge-red',       'At Risk'],
  };
  const [cls, txt] = map[label] || ['badge-secondary', label];
  return `<span class="badge ${cls}">${txt}</span>`;
}

