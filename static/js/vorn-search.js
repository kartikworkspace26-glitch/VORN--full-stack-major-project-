/**
 * VORN — Search Overlay
 * Fullscreen search with live AJAX suggestions, keyboard navigation,
 * recent searches stored in localStorage.
 */
(function () {
  'use strict';

  const overlay    = document.getElementById('search-overlay');
  const input      = document.getElementById('search-overlay-input');
  const closeBtn   = document.getElementById('search-overlay-close');
  const resultsEl  = document.getElementById('search-overlay-results');

  if (!overlay) return;

  let debounceTimer = null;
  const RECENT_KEY  = 'vorn_recent_searches';

  // ── Open / Close ───────────────────────────────────────────────────────────
  function openSearch() {
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    setTimeout(() => input?.focus(), 100);
    showRecent();
  }

  function closeSearch() {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
    if (input) input.value = '';
    if (resultsEl) resultsEl.innerHTML = '';
  }

  document.querySelectorAll('[data-search-trigger]').forEach((el) => {
    el.addEventListener('click', (e) => { e.preventDefault(); openSearch(); });
  });

  closeBtn?.addEventListener('click', closeSearch);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('open')) closeSearch();
    // Keyboard nav in results
    if (overlay.classList.contains('open')) handleKeyNav(e);
  });

  // Click backdrop to close
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeSearch();
  });

  // ── Live Search ────────────────────────────────────────────────────────────
  input?.addEventListener('input', () => {
    const q = input.value.trim();
    clearTimeout(debounceTimer);
    if (!q) { showRecent(); return; }
    debounceTimer = setTimeout(() => fetchResults(q), 300);
  });

  function fetchResults(q) {
    if (!resultsEl) return;
    resultsEl.innerHTML = '<div class="search-no-results"><i class="fa fa-spinner fa-spin" style="color:var(--gold);font-size:1.5rem;"></i></div>';

    fetch(`/shop/search/?q=${encodeURIComponent(q)}&format=json`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.json())
    .then(data => {
      if (!data.products || data.products.length === 0) {
        resultsEl.innerHTML = `<div class="search-no-results">No results for "<em style="color:var(--gold)">${q}</em>"</div>`;
        return;
      }
      resultsEl.innerHTML = data.products.slice(0, 8).map((p, i) => `
        <a href="${p.url}" class="search-result-item" data-index="${i}">
          ${p.image ? `<img class="search-result-img" src="${p.image}" alt="${p.name}" loading="lazy">` : '<div class="search-result-img" style="background:var(--black-elevated);"></div>'}
          <div>
            <div class="search-result-name">${p.name}</div>
            <div class="search-result-price">₹${parseFloat(p.price).toLocaleString('en-IN', {minimumFractionDigits: 0})}</div>
          </div>
        </a>`).join('');
      bindResultClicks(q);
    })
    .catch(() => {
      resultsEl.innerHTML = '<div class="search-no-results">Search unavailable. <a href="/shop/search/?q=' + encodeURIComponent(q) + '" style="color:var(--gold)">Browse results →</a></div>';
    });
  }

  function bindResultClicks(q) {
    resultsEl?.querySelectorAll('.search-result-item').forEach((el) => {
      el.addEventListener('click', () => saveRecent(q));
    });
  }

  // ── Recent Searches ────────────────────────────────────────────────────────
  function getRecent() {
    try { return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]'); }
    catch { return []; }
  }

  function saveRecent(q) {
    if (!q) return;
    let recent = getRecent().filter(r => r !== q);
    recent.unshift(q);
    recent = recent.slice(0, 5);
    localStorage.setItem(RECENT_KEY, JSON.stringify(recent));
  }

  function showRecent() {
    if (!resultsEl) return;
    const recent = getRecent();
    if (recent.length === 0) { resultsEl.innerHTML = ''; return; }
    resultsEl.innerHTML = `
      <div style="font-size:0.58rem;letter-spacing:0.3em;text-transform:uppercase;color:var(--gold);margin-bottom:12px;">Recent Searches</div>
      ${recent.map(q => `
        <a href="/shop/search/?q=${encodeURIComponent(q)}" class="search-result-item">
          <i class="fa fa-clock-rotate-left" style="color:var(--gray-500);font-size:0.9rem;width:48px;text-align:center;"></i>
          <div class="search-result-name" style="font-size:0.95rem;">${q}</div>
        </a>`).join('')}`;
  }

  // ── Keyboard Navigation ────────────────────────────────────────────────────
  function handleKeyNav(e) {
    if (!resultsEl) return;
    const items = [...resultsEl.querySelectorAll('.search-result-item')];
    if (!items.length) return;
    const focused = document.activeElement;
    const idx = items.indexOf(focused);
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      items[idx + 1 < items.length ? idx + 1 : 0]?.focus();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (idx <= 0) input?.focus();
      else items[idx - 1]?.focus();
    } else if (e.key === 'Enter' && focused.href) {
      focused.click();
    }
  }

  // ── Form Submit ────────────────────────────────────────────────────────────
  document.getElementById('search-overlay-form')?.addEventListener('submit', (e) => {
    const q = input?.value.trim();
    if (q) saveRecent(q);
  });

  window.VornSearch = { open: openSearch, close: closeSearch };
})();
