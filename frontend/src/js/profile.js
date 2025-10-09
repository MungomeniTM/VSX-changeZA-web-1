// profile.js — full profile UI & upload wiring
const $ = id => document.getElementById(id);
const create = (tag, cls) => { const e = document.createElement(tag); if (cls) e.className = cls; return e; };
const API = window.API;
const auth = window.auth;

// state
let state = { skills: [], portfolio: [], photos: [], companies: [], discoverable: true, userId: null };

// helpers
function safeText(v, fallback='') { return v ? String(v) : fallback; }

// DOM refs
const skillText = $('skillText');
const skillsInput = $('skillsInput');
const portfolioUrl = $('portfolioUrl');
const addPortfolioBtn = $('addPortfolio');
const portfolioList = $('portfolioList');
const portfolioPreview = $('portfolioPreview');

const fileInput = $('fileInput');
const dropzone = $('dropzone');
const dzPreview = $('dzPreview');
const chooseFiles = $('chooseFiles');

const companiesInput = $('companyUrl');
const addCompanyBtn = $('addCompany');
const companiesAdded = $('companiesAdded');

const photosGallery = $('photosGallery');
const mediaModal = $('mediaModal');
const mediaViewer = $('mediaViewer');
const closeModal = $('closeModal');

const toggleDiscover = $('toggleDiscover');
const discoverState = $('discoverState');

const avatarUrl = $('avatarUrl');
const pAvatar = $('pAvatar');
const pName = $('pName');
const pRole = $('pRole');
const pLocation = $('pLocation');

const saveBtn = $('saveProfile');
const profileForm = $('profileForm');
const profileMsg = $('profileMsg');

// Render helpers
function renderSkills() {
  // clear existing tags (except input)
  Array.from(skillsInput.querySelectorAll('.tag')).forEach(n=>n.remove());
  state.skills.forEach((s,i) => {
    const tag = create('span','tag'); tag.textContent = s;
    const btn = create('button'); btn.type='button'; btn.textContent='✕'; btn.addEventListener('click', () => { state.skills.splice(i,1); renderSkills(); });
    tag.appendChild(btn); skillsInput.insertBefore(tag, skillText);
  });
}

function renderPortfolioList() {
  portfolioList.innerHTML='';
  portfolioPreview.innerHTML='';
  if (!state.portfolio.length) { portfolioPreview.textContent='No links yet'; return; }
  state.portfolio.forEach((u,i) => {
    const it = create('div','portfolio-item');
    const media = create('div'); media.style.flex='0 0 96px';
    const img = create('img'); img.src = (/\.(jpg|jpeg|png|gif|webp)$/i.test(u) ? u : ''); img.alt = u;
    if (img.src) media.appendChild(img);
    else media.textContent='🔗';
    it.appendChild(media);
    const info = create('div'); info.style.flex='1';
    const a = create('a'); a.href = u; a.textContent = u; a.target='_blank';
    info.appendChild(a);
    it.appendChild(info);
    const rm = create('button','btn ghost'); rm.type='button'; rm.textContent='Remove'; rm.addEventListener('click', ()=>{ state.portfolio.splice(i,1); renderPortfolioList(); });
    it.appendChild(rm);
    portfolioList.appendChild(it);

    // preview small
    const pv = create('div','portfolio-item'); const mini = img.cloneNode(true);
    if (mini.src) pv.appendChild(mini); else pv.textContent = u;
    portfolioPreview.appendChild(pv);
  });
}

function renderCompanies() {
  companiesAdded.innerHTML='';
  if (!state.companies.length) { companiesAdded.textContent = 'No websites yet'; return; }
  state.companies.forEach((u,i) => {
    const el = create('div','company');
    const a = create('a'); a.href = u; a.textContent = u; a.target='_blank';
    const rm = create('button','btn ghost'); rm.type='button'; rm.textContent='Remove'; rm.addEventListener('click', ()=>{ state.companies.splice(i,1); renderCompanies(); });
    el.appendChild(a); el.appendChild(rm);
    companiesAdded.appendChild(el);
  });
}

function renderPhotosGallery() {
  photosGallery.innerHTML='';
  if (!state.photos.length) { photosGallery.textContent = 'No photos yet'; return; }
  state.photos.forEach((url, i) => {
    const item = create('div','gallery-item');
    let media;
    if (/\.(jpe?g|png|gif|webp)$/i.test(url)) { media = create('img'); media.src = url; }
    else if (/\.mp4|\.webm|youtube|vimeo/i.test(url)) { media = create('video'); media.src = url; media.controls = false; }
    else { media = create('img'); }
    item.appendChild(media);
    item.addEventListener('click', ()=> openMediaModal(url));
    const rm = create('button','dz-remove'); rm.textContent='✕'; rm.addEventListener('click', (e)=>{ e.stopPropagation(); state.photos.splice(i,1); renderPhotosGallery(); });
    rm.style.position='absolute'; rm.style.right='8px'; rm.style.top='8px'; rm.style.background='rgba(0,0,0,0.4)'; rm.style.color='white'; rm.style.border='0'; rm.style.padding='4px 8px'; rm.style.borderRadius='6px';
    item.appendChild(rm);
    photosGallery.appendChild(item);
  });
}

function openMediaModal(url) {
  mediaViewer.innerHTML='';
  if (/\.mp4|\.webm|youtube|vimeo/i.test(url)) {
    const v = create('video'); v.src=url; v.controls = true; v.className='media'; mediaViewer.appendChild(v);
  } else {
    const img = create('img'); img.src=url; img.className='media'; mediaViewer.appendChild(img);
  }
  mediaModal.classList.remove('hidden'); mediaModal.style.display='flex'; mediaModal.setAttribute('aria-hidden','false');
}

closeModal.addEventListener('click', ()=> { mediaModal.classList.add('hidden'); mediaModal.style.display='none'; mediaViewer.innerHTML=''; mediaModal.setAttribute('aria-hidden','true'); });

// skills input
skillText.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    const v = skillText.value.trim(); if (v && !state.skills.includes(v)) state.skills.push(v); skillText.value=''; renderSkills();
  }
});

// portfolio add
addPortfolioBtn.addEventListener('click', ()=> {
  const v = portfolioUrl.value.trim(); if (!v) return; state.portfolio.push(v); portfolioUrl.value=''; renderPortfolioList();
});

// company add
addCompanyBtn.addEventListener('click', ()=> {
  const v = companiesInput.value.trim();
  if (!v) return;
  // quick URL normalization
  const url = v.startsWith('http') ? v : `https://${v}`;
  state.companies.push(url);
  companiesInput.value=''; renderCompanies();
});

// dropzone handlers
chooseFiles.addEventListener('click', ()=> fileInput.click());
dropzone.addEventListener('dragover', (e)=> { e.preventDefault(); dropzone.classList.add('dz-hover'); });
dropzone.addEventListener('dragleave', ()=> dropzone.classList.remove('dz-hover'));
dropzone.addEventListener('drop', async (e)=> {
  e.preventDefault(); dropzone.classList.remove('dz-hover');
  const files = Array.from(e.dataTransfer.files || []);
  await uploadFiles(files);
});

fileInput.addEventListener('change', async (e)=> {
  const files = Array.from(e.target.files || []);
  await uploadFiles(files);
});

// upload helper -> POST /api/upload multiple files
async function uploadFiles(files) {
  if (!files.length) return;
  // show small previews and upload progress
  files.forEach(f => {
    const thumb = create('div'); thumb.className='dz-thumb';
    const img = create('img'); img.src = URL.createObjectURL(f); img.style.width='100%'; img.style.height='100%'; thumb.appendChild(img);
    const rm = create('button'); rm.className='dz-remove'; rm.textContent='✕'; thumb.appendChild(rm);
    dzPreview.appendChild(thumb);
  });

  for (const f of files) {
    try {
      const form = new FormData(); form.append('file', f);
      const res = await fetch(`${window.API_BASE || ''}/api/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` },
        body: form
      });
      if (!res.ok) { console.warn('upload failed', await res.text()); continue; }
      const json = await res.json();
      if (json.url) {
        state.photos.push(json.url);
        renderPhotosGallery();
      }
    } catch (err) {
      console.error('upload error', err);
    }
  }
  dzPreview.innerHTML='';
}

// toggle discover
toggleDiscover.addEventListener('click', ()=> {
  state.discoverable = !state.discoverable;
  discoverState.textContent = state.discoverable ? 'Public' : 'Hidden';
  toggleDiscover.textContent = state.discoverable ? 'Make private' : 'Make public';
});

// save profile
profileForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  profileMsg.textContent = 'Saving…';
  saveBtn.disabled = true;
  try {
    const payload = {
      firstName: $('firstName').value.trim(),
      lastName: $('lastName').value.trim(),
      role: $('role').value,
      location: $('location').value.trim(),
      bio: $('bio').value.trim(),
      rate: $('rate').value ? Number($('rate').value) : null,
      availability: $('availability').value.trim(),
      skills: state.skills,
      portfolio: state.portfolio,
      photos: state.photos,
      companies: state.companies,
      avatarUrl: $('avatarUrl').value.trim(),
      discoverable: state.discoverable
    };
    const res = await API.request('/me', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (!res.ok) {
      const txt = await res.text().catch(()=> 'save error');
      profileMsg.textContent = `Save failed: ${txt}`;
      saveBtn.disabled = false;
      return;
    }
    const updated = await res.json();
    populate(updated);
    profileMsg.textContent = 'Profile saved.';
  } catch (err) {
    console.error('save err', err);
    profileMsg.textContent = 'Network error while saving.';
  } finally {
    saveBtn.disabled = false;
    setTimeout(()=> profileMsg.textContent = '', 3000);
  }
});

// cancel => reload profile
$('cancelProfile').addEventListener('click', (e)=> { e.preventDefault(); loadProfile(); });

// populate form with profile data
function populate(profile) {
  if (!profile) return;
  state.userId = profile.id;
  $('firstName').value = profile.firstName || '';
  $('lastName').value = profile.lastName || '';
  $('role').value = profile.role || '';
  $('location').value = profile.location || '';
  $('bio').value = profile.bio || '';
  $('rate').value = profile.rate || '';
  $('availability').value = profile.availability || '';
  state.skills = Array.isArray(profile.skills) ? profile.skills : (profile.skills ? JSON.parse(profile.skills) : []);
  state.portfolio = Array.isArray(profile.portfolio) ? profile.portfolio : (profile.portfolio ? JSON.parse(profile.portfolio) : []);
  state.photos = Array.isArray(profile.photos) ? profile.photos : (profile.photos ? JSON.parse(profile.photos) : []);
  state.companies = Array.isArray(profile.companies) ? profile.companies : (profile.companies ? JSON.parse(profile.companies) : []);
  state.discoverable = profile.discoverable === undefined ? true : !!profile.discoverable;

  $('avatarUrl').value = profile.avatarUrl || '';
  pName.textContent = `${profile.firstName || ''} ${profile.lastName || ''}`.trim() || 'User';
  pRole.textContent = profile.role || '—';
  pLocation.textContent = profile.location || '—';
  if (profile.avatarUrl) { pAvatar.style.backgroundImage = `url(${profile.avatarUrl})`; pAvatar.textContent=''; } else { pAvatar.style.backgroundImage=''; pAvatar.textContent = (profile.firstName || 'U').charAt(0).toUpperCase(); }

  renderSkills(); renderPortfolioList(); renderCompanies(); renderPhotosGallery();
  discoverState.textContent = state.discoverable ? 'Public' : 'Hidden';
  toggleDiscover.textContent = state.discoverable ? 'Make private' : 'Make public';
}

// load /me
async function loadProfile() {
  try {
    const res = await API.request('/me', { method: 'GET' });
    if (!res.ok) throw new Error('not ok');
    const data = await res.json();
    populate(data);
  } catch (err) {
    console.warn('load profile', err);
    profileMsg.textContent = 'Could not load profile — check backend.';
  }
}

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


// initial guard
(async function init(){
  if (!auth.getToken()) { location.href = './login.html'; return; }
  await loadProfile();
})();