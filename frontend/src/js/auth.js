// ===========================
// API BASE URL
// ===========================
const API_URL = "http://127.0.0.1:5000"; // Backend running on 5000

// ===========================
// AUTH UTILITIES
// ===========================
window.auth = {
  getToken: () => localStorage.getItem("token"),
  getUser: () => JSON.parse(localStorage.getItem("user") || "{}"),
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "login.html";
  }
};

// ===========================
// EVENT LISTENERS
// ===========================
document.addEventListener("DOMContentLoaded", () => {

// ---------------------------
// REGISTER
// ---------------------------
const registerForm = document.getElementById("registerForm");
if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const fullName = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const role = document.getElementById("role").value;

    if (!role) return alert("Please select a role");
    if (password !== confirmPassword) return alert("Passwords do not match");

    // 🧠 Split full name into first and last names
    const [first_name, ...rest] = fullName.split(" ");
    const last_name = rest.join(" ") || "";

    try {
      const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ first_name, last_name, email, password, role }),
      });

      const data = await res.json();

      if (res.ok) {
        console.log("✅ Registered successfully:", data);
        alert("Registration successful! Redirecting to login…");
        window.location.href = "login.html";
      } else {
        console.error("❌ Registration failed:", data);
        alert(`Registration failed: ${data.error || data.message || data.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("⚠️ Register error:", err);
      alert("Server error: Unable to reach API. Make sure backend is running on port 5000.");
    }
  });
}

  // ---------------------------
  // LOGIN
  // ---------------------------
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;

      try {
        const res = await fetch(`${API_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });

        const data = await res.json();

        if (res.ok) {
          localStorage.setItem("token", data.token);
          localStorage.setItem("user", JSON.stringify(data.user));
          console.log("✅ Login successful:", data);
          window.location.href = "dashboard.html"; // Redirect to dashboard
        } else if (res.status === 401) {
          console.warn("⚠️ Invalid credentials");
          alert("Invalid email or password");
        } else {
          console.error("❌ Login failed:", data);
          alert(`Login failed: ${data.detail || "Unknown error"}`);
        }
      } catch (err) {
        console.error("⚠️ Login error:", err);
        alert("Server error: Unable to reach API. Make sure backend is running on port 5000.");
      }
    });
  }

  // Add password toggles + live match feedback
  function addPasswordToggle(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const wrap = document.createElement('div');
    wrap.className = 'pw-wrap';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pw-toggle';
    btn.textContent = '👁';
    btn.addEventListener('click', () => {
      input.type = input.type === 'password' ? 'text' : 'password';
      btn.textContent = input.type === 'password' ? '👁' : '👁';
    });
    wrap.appendChild(btn);
  }

  // Show/hide for login and register
  addPasswordToggle('password');
  addPasswordToggle('confirmPassword');

  // live match indicator for register
  const pw = document.getElementById('password');
  const cpw = document.getElementById('confirmPassword');
  if (cpw) {
    const matchEl = document.createElement('div');
    matchEl.className = 'pw-match';
    cpw.parentNode.appendChild(matchEl);

    function updateMatch() {
      if (!pw.value && !cpw.value) { matchEl.textContent = ''; matchEl.className = 'pw-match'; return; }
      if (pw.value === cpw.value) { matchEl.textContent = 'Passwords match'; matchEl.classList.add('match'); matchEl.classList.remove('nomatch'); }
      else { matchEl.textContent = 'Passwords do not match'; matchEl.classList.add('nomatch'); matchEl.classList.remove('match'); }
    }
    pw?.addEventListener('input', updateMatch);
    cpw?.addEventListener('input', updateMatch);
  }
});
