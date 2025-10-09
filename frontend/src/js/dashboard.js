// dashboard.js — Cosmic Alien Edition
// flawless integration: feed, profile, posts, analytics, sidepanel

const $ = id => document.getElementById(id);
const create = (tag, cls) => { const el = document.createElement(tag); if (cls) el.className = cls; return el; };

const API = window.API;
const auth = window.auth;
const H = window.helpers;

// state
let page = 1, size = 12, loading = false, hasMore = true;
let skillsChart = null, farmChart = null;

// safe API + redirect if unauthorized
async function safeJson(path, opts = {}) {
  try {
    const res = await API.request(path, opts);
    if (res.status === 401) {
      auth.logout();
      location.href = './login.html';
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

// =======================
// Profile
// =======================
async function loadProfile() {
  try {
    const user = await safeJson('/me', { method: 'GET' });
    $('userName').textContent = `${H.safeText(user.firstName)} ${H.safeText(user.lastName)}`.trim() || 'User';
    $('userRole').textContent = `${H.safeText(user.role, '—')} • ${H.safeText(user.location, '—')}`;
    $('avatar').textContent = (user.firstName || 'U').charAt(0).toUpperCase();
    if (user.id) $('profileLink').href = `./profile.html?id=${encodeURIComponent(user.id)}`;
  } catch {
    // handled by safeJson already
  }
}

// =======================
// Feed
// =======================
function renderPostCard(p) {
  const article = create('article', 'post-card card');
  article.dataset.id = p.id || '';
  const initials = H.safeText(p.user?.firstName || p.user?.name || 'U').charAt(0).toUpperCase();
  const createdAt = p.createdAt ? new Date(p.createdAt).toLocaleString() : '';
  article.innerHTML = `
    <div class="post-meta">
      <div class="avatar small">${H.escape(initials)}</div>
      <div>
        <div class="author">${H.escape(p.user?.name || p.user?.username || 'Unknown')}</div>
        <div class="muted small">${H.escape(createdAt)}</div>
      </div>
    </div>
    <div class="post-body">${H.escape(p.text || '')}</div>
    ${p.media ? (p.mediaType === 'video'
      ? `<video controls src="${H.escape(p.media)}" style="max-width:100%;margin-top:8px;border-radius:8px"></video>`
      : `<img src="${H.escape(p.media)}" alt="post media" style="max-width:100%;margin-top:8px;border-radius:8px">`) : ''}
    <div class="post-actions" style="margin-top:10px;display:flex;gap:8px;align-items:center">
      <button class="btn ghost approve-btn" data-id="${p.id}">❤️ ${p.approvals||0}</button>
      <button class="btn ghost comment-btn" data-id="${p.id}">💬 ${(p.comments||[]).length}</button>
      <button class="btn ghost share-btn" data-id="${p.id}">🔁 ${p.shares||0}</button>
    </div>
    <div class="comments-section" id="comments-${p.id}" hidden></div>
  `;
  return article;
}

async function loadFeed() {
  if (loading || !hasMore) return;
  loading = true;
  $('loader').classList.remove('hidden');
  try {
    const payload = await safeJson(`/posts?page=${page}&limit=${size}`, { method: 'GET' });
    const posts = Array.isArray(payload.posts) ? payload.posts : (Array.isArray(payload) ? payload : []);
    posts.forEach(p => $('feed').appendChild(renderPostCard(p)));
    page++;
    hasMore = (payload.hasMore !== undefined) ? payload.hasMore : (posts.length === size);
  } catch (err) {
    console.warn('loadFeed error', err);
    if (page === 1) {
      const msg = create('div','card'); msg.textContent = 'Unable to load feed right now.';
      $('feed').appendChild(msg);
    }
    hasMore = false;
  } finally {
    loading = false;
    $('loader').classList.add('hidden');
  }
}

// =======================
// Composer (Post creation)
// =======================
function resetComposer() {
  $('composeText').value = '';
  $('composeFile').value = '';
  $('fileName').textContent = 'No file chosen';
  $('preview').hidden = true;
  $('previewMedia').innerHTML = '';
}

$('composeFile').addEventListener('change', (ev) => {
  const f = ev.target.files[0];
  $('fileName').textContent = f ? f.name : 'No file chosen';
});

$('previewBtn').addEventListener('click', () => {
  const f = $('composeFile').files[0];
  if (!f) return alert('No file selected');
  const url = URL.createObjectURL(f);
  const fig = $('previewMedia'); fig.innerHTML = '';
  if (f.type.startsWith('image/')) {
    const img = create('img'); img.src = url; img.alt = f.name; img.style.maxWidth = '100%'; fig.appendChild(img);
  } else if (f.type.startsWith('video/')) {
    const v = create('video'); v.controls = true; v.src = url; v.style.maxWidth = '100%'; fig.appendChild(v);
  } else {
    fig.textContent = 'Unsupported file type';
  }
  $('preview').hidden = false;
});

$('postBtn').addEventListener('click', async () => {
  const text = $('composeText').value.trim();
  const file = $('composeFile').files[0];
  if (!text && !file) { alert('Please write something or attach a file.'); return; }
  $('postBtn').disabled = true;
  try {
    const form = new FormData();
    form.append('text', text);
    if (file) form.append('media', file);
    const res = await API.request('/posts', { method: 'POST', body: form, skipJson: true });
    if (!res.ok) throw new Error('post failed');
    const created = await res.json();
    $('feed').prepend(renderPostCard(created));
    resetComposer();

    // sync with analytics + sidepanel
    userData.listings.push(`🆕 ${created.text || 'New Post'}`);
    renderPanel("listings");
    updateAnalytics();
  } catch (err) {
    console.error('post error', err);
    alert('Could not create post. Check backend.');
  } finally {
    $('postBtn').disabled = false;
  }
});

// =======================
// Feed actions (Approve, Comment, Share)
// =======================
$('feed').addEventListener('click', async (ev) => {
  const likeBtn = ev.target.closest('.approve-btn');
  if (likeBtn) {
    const id = likeBtn.dataset.id;
    try {
      const res = await API.request(`/posts/${id}/approve`, { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        likeBtn.textContent = `❤️ ${updated.approvals || 0}`;
      }
    } catch (err) { console.warn('approve failed', err); }
    return;
  }
  const commentBtn = ev.target.closest('.comment-btn');
  if (commentBtn) {
    const id = commentBtn.dataset.id;
    const box = $(`comments-${id}`);
    if (!box) return;
    box.hidden = !box.hidden;
    if (!box.hidden && box.childElementCount === 0) {
      try {
        const r = await API.request(`/posts/${id}/comments`, { method: 'GET' });
        if (r.ok) {
          const comments = await r.json();
          comments.forEach(c => {
            const p = create('p'); p.className = 'muted'; p.textContent = `${c.user?.name || 'User'}: ${c.text}`;
            box.appendChild(p);
          });
          const ta = create('textarea'); ta.rows=2; ta.placeholder='Write a comment...';
          const b = create('button','btn primary'); b.textContent='Comment';
          b.addEventListener('click', async () => {
            const content = ta.value.trim(); if (!content) return;
            try {
              const rr = await API.request(`/posts/${id}/comments`, { method: 'POST', body: JSON.stringify({ text: content }), headers: {'Content-Type':'application/json'} });
              if (rr.ok) {
                const created = await rr.json();
                const p = create('p'); p.className='muted'; p.textContent = `${created.user?.name || 'User'}: ${created.text}`;
                box.insertBefore(p, ta);
                ta.value = '';
              }
            } catch { alert('Could not post comment'); }
          });
          const wrap = create('div'); wrap.style.marginTop = '8px'; wrap.appendChild(ta); wrap.appendChild(b);
          box.appendChild(wrap);
        }
      } catch (err) { console.warn('comments load failed', err); }
    }
    return;
  }
  const shareBtn = ev.target.closest('.share-btn');
  if (shareBtn) {
    const id = shareBtn.dataset.id;
    try {
      await navigator.clipboard.writeText(`${location.origin}/posts/${id}`);
      alert('Post link copied.');
    } catch {
      alert(`Shareable link: ${location.origin}/posts/${id}`);
    }
    return;
  }
});

// =======================
// Infinite Scroll
// =======================
window.addEventListener('scroll', () => {
  if ((window.innerHeight + window.scrollY) >= (document.body.offsetHeight - 300)) {
    loadFeed();
  }
});

// =======================
// Search
// =======================
const doSearch = H.debounce(async () => {
  const q = $('globalSearch').value.trim();
  const resultsEl = $('searchResults');
  if (!q) { resultsEl.style.display = 'none'; resultsEl.innerHTML = ''; return; }
  resultsEl.style.display = 'block';
  resultsEl.innerHTML = '<li class="muted">Searching…</li>';
  try {
    const r = await API.request(`/search?q=${encodeURIComponent(q)}`, { method: 'GET' });
    if (!r.ok) throw new Error('search failed');
    const hits = await r.json();
    if (!Array.isArray(hits) || hits.length === 0) { resultsEl.innerHTML = '<li class="muted">No results</li>'; return; }
    resultsEl.innerHTML = '';
    hits.forEach(h => {
      const li = create('li'); li.tabIndex = 0;
      li.textContent = `${h.name || h.title} • ${h.type || h.skill || ''}`;
      li.addEventListener('click', () => { location.href = `./profile.html?id=${encodeURIComponent(h.id)}`; });
      resultsEl.appendChild(li);
    });
  } catch {
    resultsEl.innerHTML = '<li class="muted">Search failed</li>';
  }
}, 300);

$('globalSearch').addEventListener('input', doSearch);
$('searchBtn').addEventListener('click', doSearch);

// =======================
// Geolocation
// =======================
$('enableGeo').addEventListener('click', () => {
  if (!navigator.geolocation) return alert('Geolocation not supported');
  $('nearbyList').innerHTML = '<li class="muted">Finding projects near you…</li>';
  navigator.geolocation.getCurrentPosition(async pos => {
    try {
      const r = await API.request(`/nearby?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`, { method: 'GET' });
      if (!r.ok) throw new Error('nearby failed');
      const list = await r.json();
      $('nearbyList').innerHTML = '';
      list.forEach(p => { const li = create('li'); li.textContent = `${p.title} • ${p.distance || '—'}`; $('nearbyList').appendChild(li); });
    } catch {
      $('nearbyList').innerHTML = '<li class="muted">Could not find nearby projects.</li>';
    }
  }, () => { $('nearbyList').innerHTML = '<li class="muted">Location permission denied.</li>'; }, { timeout: 15000 });
});

// =======================
// Analytics + SidePanel
// =======================
const sidePanel = $('sidePanel');
const linkBtns = document.querySelectorAll('.link-btn');

const userData = {
  skills: ["Welding", "Plumbing", "App Development"],
  listings: ["Service: Plumbing (R500)", "Farm: 20 bags of maize"],
  requests: ["Need an electrician in Pretoria", "Looking for UI designer"]
};

function renderPanel(section) {
  let html = "";
  if (section === "skills") html = `<h5>My Skills</h5><ul>${userData.skills.map(s=>`<li>🔹 ${s}</li>`).join("")}</ul>`;
  if (section === "listings") html = `<h5>My Listings</h5><ul>${userData.listings.map(i=>`<li>📦 ${i}</li>`).join("")}</ul>`;
  if (section === "requests") html = `<h5>Exchange Requests</h5><ul>${userData.requests.map(r=>`<li>🔄 ${r}</li>`).join("")}</ul>`;
  sidePanel.innerHTML = html;
  sidePanel.classList.remove("hidden");
}
linkBtns.forEach(btn => btn.addEventListener("click", () => renderPanel(btn.dataset.section)));

function updateAnalytics() {
  $('statUsers').textContent = "128";
  $('statPosts').textContent = String(Number($('statPosts').textContent || 0) + 1);
  $('statFarms').textContent = "76";
  $('kpi1').textContent = "↑ 42%";
  $('kpi2').textContent = "↑ 18%";
  $('kpi3').textContent = "120+";
}
updateAnalytics();

// =======================
// Wire controls
// =======================
$('logout').addEventListener('click', async () => {
  try { await API.request('/auth/logout', { method: 'POST' }); } catch {}
  auth.logout();
});
$('createPostSidebar').addEventListener('click', () => { window.scrollTo({ top: 200, behavior: 'smooth' }); $('composeText').focus(); });
$('fab').addEventListener('click', () => { $('composeText').focus(); });

// theme toggle
(function themeInit(){
  const root = document.documentElement;
  const stored = localStorage.getItem('vsx-theme') || 'dark';
  root.setAttribute('data-theme', stored);
  $('toggleTheme').addEventListener('click', () => {
    const cur = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', cur);
    localStorage.setItem('vsx-theme', cur);
    $('toggleTheme').setAttribute('aria-pressed', cur === 'dark' ? 'false' : 'true');
  });
})();

// =======================
// Init
// =======================
(async function init() {
  if (!auth.getToken()) { location.href = './login.html'; return; }
  await Promise.allSettled([loadProfile(), loadFeed()]);
})();
const authUser = auth.getUser();

// Redirect to login if not logged in
if (!auth.getToken() || !authUser.email) {
  window.location.href = "login.html";
}

// Cosmic role-based greeting
const userNameEl = document.getElementById("userName");
const userRoleEl = document.getElementById("userRole");

if (authUser) {
  userNameEl.textContent = authUser.name || `${authUser.firstName || 'User'}`;
  userRoleEl.textContent = `${authUser.role || '—'} • ${authUser.location || '—'}`;
}
window.API = {
  request: async (path, opts = {}) => {
    opts.headers = opts.headers || {};
    const token = auth.getToken();
    if (token) opts.headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_URL}${path}`, opts);
    return res;
  },
  json: async (path, opts = {}) => {
    const res = await window.API.request(path, opts);
    return res.ok ? res.json() : null;
  }
};
