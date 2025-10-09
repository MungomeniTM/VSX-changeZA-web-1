// helpers.js — small utilities
window.helpers = {
  escape(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  },
  debounce(fn, ms = 250) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  },
  formatPct(n) { return (typeof n === 'number') ? `${Math.round(n)}%` : '—'; },
  safeText(s, fallback = '') { return (s === null || s === undefined) ? fallback : String(s); }
};