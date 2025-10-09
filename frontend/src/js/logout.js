// 👽 Alien-coded Logout Experience
document.addEventListener("DOMContentLoaded", () => {
  const confirmLogout = document.getElementById("confirmLogout");
  const cancelLogout = document.getElementById("cancelLogout");
  const container = document.querySelector(".logout-card");
  const canvas = document.getElementById("particleCanvas");
  const ctx = canvas.getContext("2d");

  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  // Smooth animated particle aura
  const particles = Array.from({ length: 80 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: Math.random() * 2 + 1,
    dx: (Math.random() - 0.5) * 1.5,
    dy: (Math.random() - 0.5) * 1.5,
    color: `hsl(${Math.random() * 360}, 100%, 60%)`
  }));

  function drawParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();

      p.x += p.dx;
      p.y += p.dy;

      if (p.x < 0 || p.x > canvas.width) p.dx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.dy *= -1;
    });
    requestAnimationFrame(drawParticles);
  }
  drawParticles();

  window.addEventListener("resize", () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  });

  // Logout confirmation logic
  confirmLogout.addEventListener("click", () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    sessionStorage.clear();

    container.innerHTML = `
      <h1 class="logout-message">Logging Out...</h1>
      <div class="loader"></div>
    `;

    setTimeout(() => {
      container.innerHTML = `<h1 class="logout-message">Goodbye 👋</h1>`;
    }, 1800);

    setTimeout(() => {
      window.location.href = "login.html";
    }, 3000);
  });

  // Cancel and stay logged in → back to dashboard
  cancelLogout.addEventListener("click", () => {
    container.innerHTML = `<h1 class="logout-message">Returning to Dashboard...</h1>`;
    setTimeout(() => {
      window.location.href = "dashboard.html";
    }, 1500);
  });
});