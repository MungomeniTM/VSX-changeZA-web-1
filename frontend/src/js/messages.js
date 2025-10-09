document.addEventListener("DOMContentLoaded", () => {
  const chatList = document.getElementById("chatList");
  const chatMessages = document.getElementById("chatMessages");
  const chatWith = document.getElementById("chatWith");
  const sendBtn = document.getElementById("sendBtn");
  const messageInput = document.getElementById("messageInput");

  let currentChatUser = null;

  // Temporary sample users
  const users = [
    { id: 1, name: "Alien Engineer 👽" },
    { id: 2, name: "Cosmic Builder ⚡" },
    { id: 3, name: "Quantum Collaborator 🧬" },
  ];

  users.forEach(user => {
    const div = document.createElement("div");
    div.className = "chat-user";
    div.textContent = user.name;
    div.onclick = () => openChat(user);
    chatList.appendChild(div);
  });

  function openChat(user) {
    currentChatUser = user;
    chatWith.textContent = `Chat with ${user.name}`;
    chatMessages.innerHTML = "";
  }

  sendBtn.onclick = () => {
    const text = messageInput.value.trim();
    if (!text || !currentChatUser) return;

    const msgDiv = document.createElement("div");
    msgDiv.className = "message sent";
    msgDiv.textContent = text;
    chatMessages.appendChild(msgDiv);

    messageInput.value = "";
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Simulate reply
    setTimeout(() => {
      const reply = document.createElement("div");
      reply.className = "message received";
      reply.textContent = `Received: "${text}"`;
      chatMessages.appendChild(reply);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 700);
  };
});

// frontend/public/profile.js
// Profile page script — includes theme toggle (dark <-> light) and profile loading.
// Matches the dashboard.js theme behavior and localStorage key "vsx-theme".

const $ = id => document.getElementById(id);

// external helpers (may be provided globally by your other scripts)
const API = window.API;
const auth = window.auth;
const H = window.helpers || {
  // minimal safe fallbacks in case helpers.js isn't loaded
  safeText: (v, d = "") => (v === null || v === undefined) ? d : String(v),
  escape: s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))
};

// -------------------------
// Theme toggle (same behavior as dashboard.js)
// -------------------------
function themeInit() {
  const root = document.documentElement;
  const toggle = $('toggleTheme');

  const stored = localStorage.getItem('vsx-theme') || 'dark';
  root.setAttribute('data-theme', stored);

  if (toggle) {
    // aria-pressed: keep parity with dashboard.js (dark -> 'false', light -> 'true')
    toggle.setAttribute('aria-pressed', stored === 'dark' ? 'false' : 'true');

    toggle.addEventListener('click', () => {
      const cur = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', cur);
      localStorage.setItem('vsx-theme', cur);
      toggle.setAttribute('aria-pressed', cur === 'dark' ? 'false' : 'true');
    });
  }
}

// -------------------------
// safeJson helper (like dashboard.safeJson)
// -------------------------
async function safeJson(path, opts = {}) {
  if (!API || !API.request) throw new Error('API helper not available');
  try {
    const res = await API.request(path, opts);
    // handle unauthorized centrally
    if (res.status === 401) {
      try { auth && auth.logout && auth.logout(); } catch (e) {}
      window.location.href = './login.html';
      throw new Error('unauthorized');
    }
    if (!res.ok) {
      const txt = await res.text().catch(() => `${res.status}`);
      throw new Error(`API ${res.status}: ${txt}`);
    }
    return res.json();
  } catch (err) {
    console.warn('safeJson fail', path, err);
    throw err;
  }
}

// -------------------------
// Load profile into DOM
// -------------------------
async function loadProfile() {
  if (!API || !API.request) {
    console.warn('API.request missing; cannot load profile');
    return;
  }

  try {
    const user = await safeJson('/me', { method: 'GET' });
    if (!user) return;

    const fullName = `${H.safeText(user.firstName || user.name || '', '')} ${H.safeText(user.lastName || '', '')}`.trim();
    if ($('userName')) $('userName').textContent = fullName || 'User';
    if ($('userRole')) $('userRole').textContent = `${H.safeText(user.role, '—')} • ${H.safeText(user.location, '—')}`;
    if ($('avatar')) {
      // show first initial or emoji if available
      const initial = (user.firstName || user.name || 'U').charAt(0).toUpperCase();
      $('avatar').textContent = initial;
    }

    // Optional: populate visible profile fields if present on the page
    if ($('profileEmail') && user.email) $('profileEmail').textContent = user.email;
    if ($('profileBio') && user.bio) $('profileBio').textContent = user.bio;

    // Ensure profile link points to proper id
    if (user.id && $('profileLink')) $('profileLink').href = `./profile.html?id=${encodeURIComponent(user.id)}`;
  } catch (err) {
    console.warn('Could not load profile', err);
    // keep failing silently—dashboard safeJson already redirects on 401
  }
}

// -------------------------
// Init
// -------------------------
(function init() {
  // initialize theme toggle first so UI doesn't flash wrong theme
  try { themeInit(); } catch (e) { console.warn('themeInit failed', e); }

  // redirect to login if not authenticated
    try {
      const token = auth && auth.getToken && auth.getToken();
      // You can add logic here to redirect if token is missing
    } catch (e) {
      console.warn('auth check failed', e);
    }
  
    // Optionally, load profile if on profile page
    try { loadProfile(); } catch (e) { console.warn('loadProfile failed', e); }
  })();

