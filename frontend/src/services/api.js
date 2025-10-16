// api.js — robust API wrapper (no-404; configurable base)
(function () {
  // change this if your backend runs on another host/port
  const DEFAULT = (location.hostname === 'localhost') ? 'http://127.0.0.1:5000/api' : '/api';
  window.API_BASE = window.API_BASE || DEFAULT;

  function ensurePath(p) {
    return p.startsWith('/') ? p : `/${p}`;
  }

  window.API = {
    async request(path, opts = {}) {
      const url = `${window.API_BASE}${ensurePath(path)}`;
      const controller = new AbortController();
      const timeout = opts.timeout || 12000;
      const headers = Object.assign({}, opts.headers || {});

      // If body is FormData, don't set JSON header
      const isForm = opts.body instanceof FormData;
      if (!opts.skipJson && !isForm && opts.body !== undefined && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
      }

      // Inject token if present
      const token = localStorage.getItem('token');
      if (token && !headers['Authorization']) headers['Authorization'] = `Bearer ${token}`;

      const timer = setTimeout(() => controller.abort(), timeout);

      try {
        const res = await fetch(url, {
          ...opts,
          headers,
          signal: controller.signal,
          credentials: opts.credentials || 'same-origin' // safer default
        });
        clearTimeout(timer);
        return res;
      } catch (err) {
        clearTimeout(timer);
        console.error('API.request error', url, err);
        throw err;
      }
    },

    // helpers
    async get(path, opts = {}) {
      return this.request(path, { method: 'GET', ...opts });
    },

    async post(path, body, opts = {}) {
      const isForm = body instanceof FormData;
      return this.request(path, {
        method: 'POST',
        body: isForm ? body : JSON.stringify(body || {}),
        skipJson: isForm,
        ...opts
      });
    },

    // convenience: fetch JSON and throw on non-ok
    async json(path, opts = {}) {
      const res = await this.request(path, opts);
      if (!res.ok) {
        const text = await res.text().catch(() => '');
        const msg = text ? text.substring(0, 120) : `${res.status} ${res.statusText}`;
        const e = new Error(`API ${res.status}: ${msg}`);
        e.response = res;
        throw e;
      }
      // attempt to parse json, fallback to null
      try {
        return await res.json();
      } catch (err) {
        return null;
      }
    }
  };
})();