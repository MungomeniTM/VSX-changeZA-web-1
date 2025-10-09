// ====== Mobile Menu ======
const mobileToggle = document.getElementById("mobile-toggle");
const navMenu = document.querySelector(".nav ul");

mobileToggle.addEventListener("click", () => {
  const expanded = mobileToggle.getAttribute("aria-expanded") === "true";
  mobileToggle.setAttribute("aria-expanded", !expanded);
  mobileToggle.classList.toggle("active");
  navMenu.classList.toggle("open");
});

// ====== Scroll Reveal ======
const revealElements = document.querySelectorAll(".reveal");

function revealOnScroll() {
  const windowHeight = window.innerHeight;
  revealElements.forEach(el => {
    const elementTop = el.getBoundingClientRect().top;
    if (elementTop < windowHeight - 100) {
      el.classList.add("active");
    }
  });
}

// Initial reveal
window.addEventListener("load", revealOnScroll);
window.addEventListener("scroll", revealOnScroll);

// ====== Smooth scroll for anchor links ======
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener("click", function(e){
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if(target) target.scrollIntoView({behavior: "smooth", block: "start"});
  });
});