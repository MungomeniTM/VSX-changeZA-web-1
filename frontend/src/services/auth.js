// auth.js — token helpers
window.auth = {
  getToken() { return localStorage.getItem('token'); },
  setToken(t) { localStorage.setItem('token', t); },
  clear() { localStorage.removeItem('token'); },
  logout() { this.clear(); location.href = './login.html'; }
};

// NOTE: for production, prefer httpOnly secure cookies instead of localStorage tokens.