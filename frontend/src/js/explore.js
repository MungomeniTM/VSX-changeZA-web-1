// frontend/public/explore.js
const $ = id => document.getElementById(id);
const tpl = id => document.getElementById(id);

const API_PREFIX = window.API && window.API.PREFIX ? window.API.PREFIX : '/api';
const API_BASE = window.API && window.API.API_BASE ? window.API.API_BASE : ''; // if set

function apiUrl(path){
  // path should be without prefix: '/users'
  return `${API_BASE}${API_PREFIX}${path}`;
}

function authHeaders(){
  const headers = {};
  const token = localStorage.getItem('token');
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

let page = 1, limit = 12, lastSkill='', lastLocation='';

// categories sample
const categories = ["Cleaning","Electricians","Carpenters","Plumbers","Painters","Pest Control","AC Repair","Legal Service","Farmers"];

function initCategories(){
  const grid = $('categoryGrid');
  categories.forEach(c=>{
    const el = document.createElement('button');
    el.className = 'category-item';
    el.textContent = c;
    el.addEventListener('click', ()=>{
      $('exploreSkill').value = c;
      doSearch(true);
    });
    grid.appendChild(el);
  });
}

function createUserCard(user){
  const tplNode = tpl('userCardTpl').content.cloneNode(true);
  const root = tplNode.querySelector('.user-card');
  const nameEl = root.querySelector('.name');
  const locEl = root.querySelector('.loc');
  const skillsEl = root.querySelector('.skills');
  const avatar = root.querySelector('.avatar');

  nameEl.textContent = `${user.firstName || ''} ${user.lastName || ''}`.trim() || 'User';
  locEl.textContent = user.location || '';
  skillsEl.textContent = (Array.isArray(user.skills) ? user.skills.slice(0,4).join(' • ') : (user.skills || []).join(' • '));
  if (user.avatarUrl) {
    avatar.style.backgroundImage = `url(${user.avatarUrl})`;
    avatar.textContent = '';
  } else {
    avatar.textContent = (user.firstName || 'U').charAt(0).toUpperCase();
  }

  // view button
  const viewBtn = root.querySelector('.viewBtn');
  viewBtn.href = `./profile.html?id=${encodeURIComponent(user.id)}`;

  // connect button (just placeholder)
  root.querySelector('.connectBtn').addEventListener('click', ()=> {
    alert(`Open chat / message flow with ${nameEl.textContent}`);
  });

  return root;
}

async function fetchUsers({ skill, location, page=1, limit=12 }){
  const params = new URLSearchParams();
  if (skill) params.set('skill', skill);
  if (location) params.set('location', location);
  params.set('page', page);
  params.set('limit', limit);

  const url = apiUrl(`/users?${params.toString()}`);
  try {
    const res = await fetch(url, { headers: { ...authHeaders() } });
    if (!res.ok) {
      console.warn('search failed', res.status);
      return { results: [] };
    }
    return await res.json();
  } catch (err) {
    console.error('network error', err);
    return { results: [] };
  }
}

async function doSearch(isNew = false){
  if (isNew) {
    page = 1;
    $('results').innerHTML = '';
  }
  const skill = $('exploreSkill').value.trim();
  const location = $('exploreLocation').value.trim();
  lastSkill = skill; lastLocation = location;

  $('resultsInfo').textContent = 'Searching…';
  const data = await fetchUsers({ skill, location, page, limit });
  const rows = data.results || [];
  if (rows.length === 0 && page === 1){
    $('results').innerHTML = `<div class="results-empty">No results found. Try widening the search.</div>`;
    $('resultsInfo').textContent = 'No matches';
    $('loadMore').style.display = 'none';
    return;
  }

  rows.forEach(u => {
    $('results').appendChild(createUserCard(u));
  });

  $('resultsInfo').textContent = `Showing ${document.querySelectorAll('.user-card').length} results`;
  $('loadMore').style.display = rows.length >= limit ? 'inline-block' : 'none';
  page++;
}

$('exploreSearch').addEventListener('click', ()=> doSearch(true));
$('loadMore').addEventListener('click', ()=> doSearch(false));

$('useMyLocation').addEventListener('click', ()=>{
  if (!navigator.geolocation) return alert('Geolocation not supported');
  $('resultsInfo').textContent = 'Finding your location…';
  navigator.geolocation.getCurrentPosition(async pos => {
    const lat = pos.coords.latitude, lng = pos.coords.longitude;
    // simple: send lat/lng as location param (you can reverse-geocode later)
    $('exploreLocation').value = `${lat.toFixed(3)},${lng.toFixed(3)}`;
    doSearch(true);
  }, (err)=> {
    alert('Could not read location: '+ (err.message || 'permission denied'));
  }, { timeout:10000 });
});

// small suggestion list (mocked)
function loadSuggestions(){
  const s = $('suggestions');
  const samples = [
    {firstName:'Lerato', lastName:'M', role:'Electrician', location:'Pretoria'},
    {firstName:'Sipho', lastName:'N', role:'Farmer', location:'Limpopo'},
    {firstName:'Aisha', lastName:'K', role:'Plumber', location:'Cape Town'}
  ];
  samples.forEach(u=>{
    const el = document.createElement('div'); el.className='suggestion';
    el.innerHTML = `<div style="flex:1"><strong>${u.firstName} ${u.lastName}</strong><div class="muted small">${u.role} • ${u.location}</div></div>
      <div><a class="btn ghost" href="./profile.html">View</a></div>`;
    s.appendChild(el);
  });
}

(function init(){
  initCategories();
  loadSuggestions();
  // load initial results (popular)
  doSearch(true).catch(()=>{});
})();

// explore.js — Cosmic Explore Edition

const root = document.documentElement;

// ========== Theme Toggle ==========
(function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  root.dataset.theme = saved;
  const toggle = $('toggleTheme');
  toggle.textContent = saved === 'dark' ? '🌗' : '☀️';
  toggle.onclick = () => {
    const current = root.dataset.theme;
    const next = current === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    toggle.textContent = next === 'dark' ? '🌗' : '☀️';
    localStorage.setItem('theme', next);
  };
})();

// ========== Explore Search ==========
$('exploreSearch').addEventListener('click', async () => {
  const skill = $('exploreSkill').value.trim();
  const loc = $('exploreLocation').value.trim();
  if (!skill && !loc) return alert('Please enter skill or location');

  $('resultsInfo').textContent = `Searching ${skill || ''} ${loc ? 'in ' + loc : ''}...`;

  // Simulated data for now
  const results = [
    { name: "John M.", skill: "Electrician", location: "Pretoria" },
    { name: "Lerato K.", skill: "Plumber", location: "Johannesburg" },
    { name: "Tshidzula M.", skill: "Full Stack Dev", location: "Limpopo" }
  ];

  const grid = $('results');
  grid.innerHTML = '';
  for (const r of results) {
    const card = document.importNode($('userCardTpl').content, true);
    card.querySelector('.name').textContent = r.name;
    card.querySelector('.loc').textContent = r.location;
    card.querySelector('.skills').textContent = r.skill;
    grid.appendChild(card);
  }

  $('resultsInfo').textContent = `${results.length} results found`;
});