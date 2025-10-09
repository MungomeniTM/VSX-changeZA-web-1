// ===========================
// API BASE URL
// ===========================
const API_URL = "http://127.0.0.1:8000"; // Backend running on 8000

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

      const name = document.getElementById("name").value.trim();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;
      const confirmPassword = document.getElementById("confirmPassword").value;
      const role = document.getElementById("role").value;

      if (!role) return alert("Please select a role");
      if (password !== confirmPassword) return alert("Passwords do not match");

      try {
        const res = await fetch(`${API_URL}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, password, role }),
        });

        const data = await res.json();

        if (res.ok) {
          console.log("✅ Registered successfully:", data);
          alert("Registration successful! Redirecting to login…");
          window.location.href = "login.html"; // Perfect redirection
        } else {
          console.error("❌ Registration failed:", data);
          alert(`Registration failed: ${data.detail || "Unknown error"}`);
        }
      } catch (err) {
        console.error("⚠️ Register error:", err);
        alert("Server error: Unable to reach API. Make sure backend is running on port 8000.");
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
        alert("Server error: Unable to reach API. Make sure backend is running on port 8000.");
      }
    });
  }
});