// VSXchangeZA Cosmic Settings 👽⚡
const $ = id => document.getElementById(id);

// THEME SYSTEM 🌗
function themeInit() {
  const root = document.documentElement;
  const toggle = $('toggleTheme');
  const stored = localStorage.getItem('vsx-theme') || 'dark';
  root.setAttribute('data-theme', stored);
  toggle.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    localStorage.setItem('vsx-theme', next);
  });
}

// USER DATA MOCK
const user = {
  name: "Neo Builder",
  email: "neo@vsxchangeza.africa",
  private: false,
  twoFA: true,
  notifications: { messages: true, approvals: true, updates: false }
};

// LOAD SETTINGS
function loadSettings() {
  $('fullName').value = user.name;
  $('email').value = user.email;
  $('privateMode').checked = user.private;
  $('twoFA').checked = user.twoFA;
  $('notifMessages').checked = user.notifications.messages;
  $('notifApprovals').checked = user.notifications.approvals;
  $('notifUpdates').checked = user.notifications.updates;
}

// SAVE SETTINGS
function saveSettings() {
  const updated = {
    name: $('fullName').value,
    email: $('email').value,
    private: $('privateMode').checked,
    twoFA: $('twoFA').checked,
    notifications: {
      messages: $('notifMessages').checked,
      approvals: $('notifApprovals').checked,
      updates: $('notifUpdates').checked
    }
  };
  console.log("Settings Saved ✅", updated);
  alert("Settings updated successfully 👽⚡");
}

// FEEDBACK
function sendFeedback() {
  const msg = $('feedback').value.trim();
  if (!msg) return alert("Please write your feedback 🪶");
  console.log("Feedback Sent 🚀", msg);
  $('feedback').value = "";
  alert("Thanks for your feedback 💫");
}

// DEVELOPER MODE 👾
function devMode() {
  const enableDev = $('enableDev');
  const devOptions = $('devOptions');
  enableDev.addEventListener('change', () => {
    devOptions.classList.toggle('hidden', !enableDev.checked);
  });

  $('aiLayout').addEventListener('click', () => alert("AI Layout Activated 🧠✨"));
  $('energyTheme').addEventListener('click', () => {
    document.body.classList.toggle('energy-active');
    alert("Live Energy Theme Activated 🌈⚡");
  });
  $('voiceControl').addEventListener('click', () => alert("Voice Control Prototype Enabled 🎙️"));
}

// INIT
(function init() {
  themeInit();
  loadSettings();
  $('saveAccount').addEventListener('click', saveSettings);
  $('sendFeedback').addEventListener('click', sendFeedback);
  $('downloadData').addEventListener('click', () => alert("Data export initiated 📦"));
  devMode();
})();