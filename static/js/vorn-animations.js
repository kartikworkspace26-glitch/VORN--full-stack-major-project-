/**
 * VORN — Animations
 * IntersectionObserver scroll reveals, parallax, staggered grids.
 */
(function () {
  'use strict';

  // ── Scroll Reveal ──────────────────────────────────────────────────────────
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  function initReveals() {
    document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale')
      .forEach((el) => revealObserver.observe(el));
  }

  // ── Staggered Product Grid ─────────────────────────────────────────────────
  function initStaggerGrid() {
    const grids = document.querySelectorAll('.stagger-grid');
    grids.forEach((grid) => {
      const cards = grid.querySelectorAll('.product-card');
      const cardObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            cards.forEach((card, i) => {
              setTimeout(() => card.classList.add('revealed'), i * 80);
            });
            obs.disconnect();
          }
        });
      }, { threshold: 0.05 });
      cardObserver.observe(grid);
      // Pre-mark cards for reveal
      cards.forEach((card) => card.classList.add('reveal'));
    });
  }

  // ── Parallax ───────────────────────────────────────────────────────────────
  let ticking = false;
  function handleParallax() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const scrollY = window.scrollY;
      document.querySelectorAll('[data-parallax]').forEach((el) => {
        const speed = parseFloat(el.dataset.parallax) || 0.3;
        const rect  = el.getBoundingClientRect();
        const centerY = rect.top + rect.height / 2 - window.innerHeight / 2;
        el.style.transform = `translateY(${centerY * speed}px)`;
      });
      ticking = false;
    });
  }

  // ── Hero Scroll Indicator ──────────────────────────────────────────────────
  function initHeroScroll() {
    const scrollBtn = document.querySelector('.hero-scroll');
    if (!scrollBtn) return;
    const target = document.getElementById('marquee-section') ||
                   document.querySelector('section:nth-of-type(2)');
    if (target) {
      scrollBtn.addEventListener('click', () => {
        target.scrollIntoView({ behavior: 'smooth' });
      });
    }
  }

  // ── Counter Animation ──────────────────────────────────────────────────────
  function animateCounter(el) {
    const target = parseInt(el.dataset.count, 10);
    const duration = 1500;
    const start = performance.now();
    function update(now) {
      const elapsed = Math.min(now - start, duration);
      const progress = elapsed / duration;
      // Ease out cubic
      const ease = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.floor(ease * target).toLocaleString();
      if (elapsed < duration) requestAnimationFrame(update);
      else el.textContent = target.toLocaleString();
    }
    requestAnimationFrame(update);
  }

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  function initCounters() {
    document.querySelectorAll('[data-count]').forEach((el) => counterObserver.observe(el));
  }

  // ── Review Bar Fill Animation ──────────────────────────────────────────────
  const barObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.querySelectorAll('.review-bar-fill').forEach((bar) => {
          bar.style.width = bar.dataset.width || '0%';
        });
        barObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });

  function initReviewBars() {
    document.querySelectorAll('.review-bars').forEach((el) => {
      el.querySelectorAll('.review-bar-fill').forEach((bar) => {
        bar.style.width = '0%';
      });
      barObserver.observe(el);
    });
  }

  // ── Marquee Pause on Hover ─────────────────────────────────────────────────
  function initMarquee() {
    const track = document.querySelector('.marquee-track');
    if (!track) return;
    track.addEventListener('mouseenter', () => track.style.animationPlayState = 'paused');
    track.addEventListener('mouseleave', () => track.style.animationPlayState = 'running');
  }

  // ── Init ───────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    initReveals();
    initStaggerGrid();
    initHeroScroll();
    initCounters();
    initReviewBars();
    initMarquee();
    window.addEventListener('scroll', handleParallax, { passive: true });
  });
})();
