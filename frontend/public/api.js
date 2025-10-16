// frontend/public/api.js
(function () {
  // Change if your backend is on a different origin/port
  const API_BASE = window.API_BASE || "http://localhost:5000";

  async function request(path, opts = {}) {
    // normalized path (ensure starts with /)
    const p = path.startsWith("/") ? path : `/${path}`;
    const url = `${API_BASE}${p}`;

    opts = Object.assign({}, opts);
    opts.headers = new Headers(opts.headers || {});

    // Add Authorization if token exists
    const token = localStorage.getItem("token");
    if (token) opts.headers.set("Authorization", `Bearer ${token}`);

    // fetch
    try {
      const res = await fetch(url, {
        method: opts.method || "GET",
        headers: opts.headers,
        body: opts.body,
        credentials: opts.credentials || "same-origin",
      });
      return res;
    } catch (err) {
      console.error("API.request network error", url, err);
      throw err;
    }
  }

  async function json(path, opts = {}) {
    const res = await request(path, opts);
    if (!res.ok) {
      const txt = await res.text().catch(() => `${res.status}`);
      const e = new Error(`API ${res.status}: ${txt}`);
      e.response = res;
      throw e;
    }
    return res.json();
  }

  window.API = { request, json, API_BASE };
})();