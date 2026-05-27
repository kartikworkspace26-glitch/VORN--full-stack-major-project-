/**
 * VORN — Catalog Filter
 * URL-synced filter state, collapsible sections, active chips, mobile drawer.
 */
(function () {
  'use strict';

  // ── Collapsible Filter Sections ────────────────────────────────────────────
  document.querySelectorAll('.filter-title[data-collapsible]').forEach((title) => {
    const section = title.closest('.filter-section');
    const body    = section?.querySelector('.filter-options, .filter-pills, .price-range');
    const icon    = title.querySelector('.filter-collapse-icon');
    if (!body) return;

    // Start open
    body.style.maxHeight = body.scrollHeight + 'px';
    body.style.overflow = 'hidden';
    body.style.transition = 'max-height 0.35s ease, opacity 0.3s';

    title.addEventListener('click', () => {
      const isOpen = body.style.maxHeight !== '0px';
      body.style.maxHeight = isOpen ? '0px' : body.scrollHeight + 'px';
      if (icon) icon.style.transform = isOpen ? 'rotate(-90deg)' : '';
    });
  });

  // ── Grid/List View Toggle ──────────────────────────────────────────────────
  const grid = document.querySelector('.product-grid');
  document.querySelectorAll('.view-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const view = btn.dataset.view;
      if (grid) {
        grid.classList.toggle('list-view', view === 'list');
      }
      localStorage.setItem('vorn_catalog_view', view);
    });
  });

  // Restore saved view
  const savedView = localStorage.getItem('vorn_catalog_view');
  if (savedView === 'list') {
    document.querySelector(`[data-view="list"]`)?.click();
  }

  // ── Mobile Filter Drawer ───────────────────────────────────────────────────
  const filterDrawer  = document.getElementById('filter-drawer');
  const drawerOverlay = document.getElementById('filter-drawer-overlay');

  document.getElementById('filter-drawer-trigger')?.addEventListener('click', () => {
    filterDrawer?.classList.add('open');
    drawerOverlay?.classList.add('open');
    document.body.style.overflow = 'hidden';
  });

  function closeFilterDrawer() {
    filterDrawer?.classList.remove('open');
    drawerOverlay?.classList.remove('open');
    document.body.style.overflow = '';
  }

  document.getElementById('filter-drawer-close')?.addEventListener('click', closeFilterDrawer);
  drawerOverlay?.addEventListener('click', closeFilterDrawer);

  // ── Active Filter Chips ────────────────────────────────────────────────────
  function buildActiveChips() {
    const container = document.getElementById('active-filters-container');
    if (!container) return;

    const params = new URLSearchParams(window.location.search);
    const chips  = [];
    const labels = {
      category: 'Category', gender: 'Gender',
      min_price: 'Min ₹', max_price: 'Max ₹',
      sort: 'Sort', is_new: 'New Arrivals', q: 'Search'
    };

    params.forEach((value, key) => {
      if (['sort', 'page'].includes(key) && key !== 'sort') return;
      if (key === 'sort' && value === '-created_at') return;
      chips.push({ key, value, label: (labels[key] || key) + ': ' + value });
    });

    if (chips.length === 0) { container.innerHTML = ''; return; }

    container.innerHTML =
      chips.map(c => `
        <button class="active-filter-chip" data-key="${c.key}" onclick="VornFilter.removeChip('${c.key}')">
          ${c.label} <span class="active-filter-chip-remove">×</span>
        </button>`).join('') +
      `<button class="clear-all-filters" onclick="VornFilter.clearAll()">Clear all (${chips.length})</button>`;
  }

  function removeChip(key) {
    const params = new URLSearchParams(window.location.search);
    params.delete(key);
    window.location.search = params.toString();
  }

  function clearAll() {
    window.location.href = window.location.pathname;
  }

  // ── Price Range Slider Label ───────────────────────────────────────────────
  const priceRange = document.getElementById('price-range-input');
  const priceLabel = document.getElementById('price-range-label');
  priceRange?.addEventListener('input', () => {
    if (priceLabel) priceLabel.textContent = '₹' + parseInt(priceRange.value).toLocaleString('en-IN');
  });

  // ── Sort Select Auto-Submit ────────────────────────────────────────────────
  document.getElementById('sort-select')?.addEventListener('change', (e) => {
    const params = new URLSearchParams(window.location.search);
    params.set('sort', e.target.value);
    params.delete('page');
    window.location.search = params.toString();
  });

  // ── Init ───────────────────────────────────────────────────────────────────
  buildActiveChips();

  window.VornFilter = { removeChip, clearAll };
})();
