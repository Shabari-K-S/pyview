/**
 * PyView Documentation Portal Client Application
 */

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initCopyButtons();
  initInstallTabs();
  initApiFilter();
  initSearch();
  initScrollSpy();
  initMobileNav();
  initInteractiveDemo();
});

/* ==========================================================================
   1. Theme Management (Dark / Light)
   ========================================================================== */
function initTheme() {
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  const themeIcon = document.getElementById("theme-icon");
  const storedTheme = localStorage.getItem("pyview-theme");
  const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

  const initialTheme = storedTheme || (systemPrefersDark ? "dark" : "dark"); // Default dark for sleek dev look
  setTheme(initialTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
      const newTheme = currentTheme === "dark" ? "light" : "dark";
      setTheme(newTheme);
    });
  }

  function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("pyview-theme", theme);
    if (themeIcon) {
      themeIcon.textContent = theme === "dark" ? "🌙" : "☀️";
    }
  }
}

/* ==========================================================================
   2. One-Click Code Copying
   ========================================================================== */
function initCopyButtons() {
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const targetSelector = btn.getAttribute("data-target");
      let textToCopy = "";

      if (targetSelector) {
        const targetEl = document.querySelector(targetSelector);
        if (targetEl) textToCopy = targetEl.textContent.trim();
      } else {
        const pre = btn.closest(".code-container")?.querySelector("pre");
        if (pre) textToCopy = pre.textContent.trim();
      }

      if (textToCopy) {
        try {
          await navigator.clipboard.writeText(textToCopy);
          const originalContent = btn.innerHTML;
          btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!`;
          btn.classList.add("copied");

          setTimeout(() => {
            btn.innerHTML = originalContent;
            btn.classList.remove("copied");
          }, 2000);
        } catch (err) {
          console.error("Failed to copy code: ", err);
        }
      }
    });
  });
}

/* ==========================================================================
   3. Installation Tabs (pip / uv / clone)
   ========================================================================== */
function initInstallTabs() {
  const tabButtons = document.querySelectorAll(".install-tab-btn");
  const commandText = document.getElementById("install-command");

  const commands = {
    uv: "uv add pyview",
    pip: "pip install pyview",
    git: "git clone https://github.com/Shabari-K-S/pyview.git",
  };

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const packageManager = btn.getAttribute("data-pm");
      if (commands[packageManager] && commandText) {
        commandText.textContent = commands[packageManager];
      }
    });
  });
}

/* ==========================================================================
   4. API Reference Filter Chips
   ========================================================================== */
function initApiFilter() {
  const filterChips = document.querySelectorAll(".api-filter-chip");
  const apiCards = document.querySelectorAll(".api-card");

  filterChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      filterChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");

      const category = chip.getAttribute("data-category");

      apiCards.forEach((card) => {
        if (category === "all" || card.getAttribute("data-category") === category) {
          card.style.display = "block";
        } else {
          card.style.display = "none";
        }
      });
    });
  });
}

/* ==========================================================================
   5. Real-time Search Filter
   ========================================================================== */
function initSearch() {
  const searchInput = document.getElementById("global-search");
  if (!searchInput) return;

  // Keyboard shortcut Ctrl+K or /
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      searchInput.focus();
    } else if (e.key === "/" && document.activeElement !== searchInput) {
      e.preventDefault();
      searchInput.focus();
    }
  });

  searchInput.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();
    const apiCards = document.querySelectorAll(".api-card");
    const exampleCards = document.querySelectorAll(".example-card");

    if (!query) {
      apiCards.forEach((card) => (card.style.display = "block"));
      exampleCards.forEach((card) => (card.style.display = "flex"));
      return;
    }

    apiCards.forEach((card) => {
      const text = card.textContent.toLowerCase();
      if (text.includes(query)) {
        card.style.display = "block";
      } else {
        card.style.display = "none";
      }
    });

    exampleCards.forEach((card) => {
      const text = card.textContent.toLowerCase();
      if (text.includes(query)) {
        card.style.display = "flex";
      } else {
        card.style.display = "none";
      }
    });
  });
}

/* ==========================================================================
   6. Sidebar ScrollSpy
   ========================================================================== */
function initScrollSpy() {
  const sections = document.querySelectorAll(".doc-section, .hero-section, .api-card");
  const navLinks = document.querySelectorAll(".sidebar-link, .toc-link");

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute("id");
          navLinks.forEach((link) => {
            if (link.getAttribute("href") === `#${id}`) {
              link.classList.add("active");
            } else {
              link.classList.remove("active");
            }
          });
        }
      });
    },
    {
      rootMargin: "-10% 0px -70% 0px",
    }
  );

  sections.forEach((section) => observer.observe(section));
}

/* ==========================================================================
   7. Mobile Navigation Toggle
   ========================================================================== */
function initMobileNav() {
  const toggleBtn = document.getElementById("mobile-nav-toggle");
  const sidebar = document.getElementById("docs-sidebar");

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });

    // Close when clicking a link inside sidebar on mobile
    sidebar.querySelectorAll(".sidebar-link").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.innerWidth <= 860) {
          sidebar.classList.remove("open");
        }
      });
    });
  }
}

/* ==========================================================================
   8. Interactive Component Playground in Hero
   ========================================================================== */
function initInteractiveDemo() {
  let count = 42;
  const counterValEl = document.getElementById("demo-counter-val");
  const counterDeltaEl = document.getElementById("demo-counter-delta");
  const incrementBtn = document.getElementById("demo-btn-inc");
  const resetBtn = document.getElementById("demo-btn-reset");

  const slider = document.getElementById("demo-slider");
  const sliderVal = document.getElementById("demo-slider-val");
  const multiplierMetric = document.getElementById("demo-metric-multiplied");

  function updateMetrics() {
    if (counterValEl) counterValEl.textContent = count;
    const factor = slider ? parseInt(slider.value, 10) : 2;
    if (multiplierMetric) multiplierMetric.textContent = count * factor;
  }

  if (incrementBtn) {
    incrementBtn.addEventListener("click", () => {
      count += 1;
      if (counterDeltaEl) {
        counterDeltaEl.textContent = "+1 (rerun computed)";
        counterDeltaEl.className = "pv-mock-metric-delta";
      }
      updateMetrics();
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      count = 0;
      if (counterDeltaEl) {
        counterDeltaEl.textContent = "Reset to 0";
        counterDeltaEl.className = "pv-mock-metric-delta neg";
      }
      updateMetrics();
    });
  }

  if (slider) {
    slider.addEventListener("input", (e) => {
      if (sliderVal) sliderVal.textContent = e.target.value;
      updateMetrics();
    });
  }
}
