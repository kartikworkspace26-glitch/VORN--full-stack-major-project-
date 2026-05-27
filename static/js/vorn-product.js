/**
 * VORN — Product Detail
 * Image gallery, zoom lens, size/color selection, sticky ATC, accordions,
 * size guide modal, quick-add.
 */
(function () {
  'use strict';

  // ── Image Gallery ──────────────────────────────────────────────────────────
  const mainImg  = document.getElementById('pdp-main-img');
  const thumbs   = document.querySelectorAll('.pdp-thumb');
  let currentIdx = 0;
  const imgUrls  = [...thumbs].map(t => t.src);

  function setImage(idx) {
    if (!mainImg || !imgUrls[idx]) return;
    currentIdx = idx;
    mainImg.style.opacity = '0';
    setTimeout(() => {
      mainImg.src = imgUrls[idx];
      mainImg.style.opacity = '1';
    }, 150);
    thumbs.forEach((t, i) => t.classList.toggle('active', i === idx));
  }

  thumbs.forEach((t, i) => {
    t.addEventListener('click', () => setImage(i));
  });

  // Prev / Next buttons
  document.getElementById('pdp-prev')?.addEventListener('click', () => {
    setImage((currentIdx - 1 + imgUrls.length) % imgUrls.length);
  });
  document.getElementById('pdp-next')?.addEventListener('click', () => {
    setImage((currentIdx + 1) % imgUrls.length);
  });

  // Keyboard gallery
  document.addEventListener('keydown', (e) => {
    if (document.getElementById('size-guide-modal')?.classList.contains('open')) return;
    if (e.key === 'ArrowLeft')  setImage((currentIdx - 1 + imgUrls.length) % imgUrls.length);
    if (e.key === 'ArrowRight') setImage((currentIdx + 1) % imgUrls.length);
  });

  // Touch swipe on main image
  let touchStartX = 0;
  mainImg?.addEventListener('touchstart', (e) => { touchStartX = e.changedTouches[0].clientX; }, { passive: true });
  mainImg?.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 50) setImage(dx < 0 ? (currentIdx + 1) % imgUrls.length : (currentIdx - 1 + imgUrls.length) % imgUrls.length);
  });

  // ── Zoom Lens ──────────────────────────────────────────────────────────────
  const zoomWrap = document.querySelector('.product-image-zoom-wrap');
  const lens     = document.querySelector('.product-image-zoom-lens');
  if (zoomWrap && lens) {
    zoomWrap.addEventListener('mousemove', (e) => {
      const rect = zoomWrap.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      lens.style.left = x + 'px';
      lens.style.top  = y + 'px';
    });
  }

  // ── Size Pills ─────────────────────────────────────────────────────────────
  document.querySelectorAll('.size-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      if (pill.classList.contains('out-of-stock')) return;
      document.querySelectorAll('.size-pill').forEach(p => p.classList.remove('selected'));
      pill.classList.add('selected');
      const sizeInput = document.getElementById('selected-size');
      if (sizeInput) sizeInput.value = pill.dataset.size;
      updateStockStatus(pill.dataset.stock);
    });
  });

  function updateStockStatus(stock) {
    const el = document.getElementById('stock-status');
    if (!el) return;
    const n = parseInt(stock, 10);
    if (n === 0)      el.innerHTML = '<span style="color:var(--danger)"><i class="fa fa-times-circle"></i> Out of Stock</span>';
    else if (n <= 3)  el.innerHTML = `<span style="color:var(--gold)"><i class="fa fa-exclamation-circle"></i> Only ${n} left</span>`;
    else if (n <= 10) el.innerHTML = `<span style="color:var(--gold)"><i class="fa fa-circle"></i> Low Stock</span>`;
    else              el.innerHTML = '<span style="color:var(--success)"><i class="fa fa-check-circle"></i> In Stock</span>';
  }

  // ── Color Swatches ─────────────────────────────────────────────────────────
  document.querySelectorAll('.color-swatch').forEach((swatch) => {
    swatch.addEventListener('click', () => {
      document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('selected'));
      swatch.classList.add('selected');
      const colorInput = document.getElementById('selected-color');
      if (colorInput) colorInput.value = swatch.dataset.color;
      const label = document.getElementById('selected-color-label');
      if (label) label.textContent = swatch.dataset.color;
    });
  });

  // ── Sticky ATC Bar ─────────────────────────────────────────────────────────
  const stickyBar = document.getElementById('sticky-atc');
  const mainAtc   = document.getElementById('main-atc-btn');
  if (stickyBar && mainAtc) {
    const atcObserver = new IntersectionObserver((entries) => {
      stickyBar.classList.toggle('visible', !entries[0].isIntersecting);
    }, { threshold: 0.5 });
    atcObserver.observe(mainAtc);
  }

  // ── Accordion ──────────────────────────────────────────────────────────────
  document.querySelectorAll('.accordion-trigger').forEach((trigger) => {
    trigger.addEventListener('click', () => {
      const item = trigger.closest('.accordion-item');
      const isOpen = item.classList.contains('open');
      // Close all
      document.querySelectorAll('.accordion-item.open').forEach(i => i.classList.remove('open'));
      if (!isOpen) item.classList.add('open');
    });
    // Open first by default
  });
  document.querySelector('.accordion-item')?.classList.add('open');

  // ── Size Guide Modal ───────────────────────────────────────────────────────
  const sizeModal = document.getElementById('size-guide-modal');
  document.querySelectorAll('[data-size-guide]').forEach((btn) => {
    btn.addEventListener('click', () => sizeModal?.classList.add('open'));
  });
  document.getElementById('size-guide-close')?.addEventListener('click', () => sizeModal?.classList.remove('open'));
  sizeModal?.addEventListener('click', (e) => { if (e.target === sizeModal) sizeModal.classList.remove('open'); });

  // Size guide tabs
  document.querySelectorAll('.size-guide-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.size-guide-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      document.querySelectorAll('.size-guide-table-panel').forEach(p => p.style.display = 'none');
      const panel = document.getElementById('size-table-' + tab.dataset.tab);
      if (panel) panel.style.display = '';
    });
  });

  // Unit toggle (cm/inches)
  document.querySelectorAll('.unit-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.unit-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const unit = btn.dataset.unit;
      document.querySelectorAll('[data-cm]').forEach((cell) => {
        cell.textContent = unit === 'cm' ? cell.dataset.cm : cell.dataset.in;
      });
    });
  });

  // ── Quick Add Modal (Catalog) ──────────────────────────────────────────────
  const quickModal = document.getElementById('quick-add-modal');
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-quick-add]');
    if (!btn || !quickModal) return;
    e.preventDefault();
    // Populate modal
    quickModal.querySelector('.quick-add-name').textContent = btn.dataset.name || '';
    quickModal.querySelector('.quick-add-price').textContent = btn.dataset.price || '';
    quickModal.querySelector('.quick-add-form').action = btn.dataset.action || '';
    quickModal.classList.add('open');
  });
  document.getElementById('quick-add-close')?.addEventListener('click', () => quickModal?.classList.remove('open'));
  quickModal?.addEventListener('click', (e) => { if (e.target === quickModal) quickModal.classList.remove('open'); });

  // ── Review Helpful ─────────────────────────────────────────────────────────
  document.querySelectorAll('.review-helpful-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      btn.disabled = true;
      btn.textContent = 'Marked!';
      btn.style.color = 'var(--success)';
    });
  });
})();
