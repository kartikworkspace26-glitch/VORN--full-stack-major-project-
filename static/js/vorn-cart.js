/**
 * VORN — Cart Drawer
 * Slide-in cart panel with AJAX add/remove/update and real-time badge.
 */
(function () {
  'use strict';

  const CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                     getCookie('csrftoken');

  function getCookie(name) {
    const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? v[2] : null;
  }

  // ── Drawer Toggle ──────────────────────────────────────────────────────────
  const drawer    = document.getElementById('cart-drawer');
  const overlay   = document.getElementById('cart-drawer-overlay');
  const closeBtn  = document.getElementById('cart-drawer-close');

  function openDrawer() {
    if (!drawer) return;
    drawer.classList.add('open');
    overlay?.classList.add('open');
    document.body.style.overflow = 'hidden';
    refreshDrawer();
  }

  function closeDrawer() {
    drawer?.classList.remove('open');
    overlay?.classList.remove('open');
    document.body.style.overflow = '';
  }

  // Open cart icon → drawer
  document.querySelectorAll('[data-cart-drawer-trigger]').forEach((el) => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      openDrawer();
    });
  });

  closeBtn?.addEventListener('click', closeDrawer);
  overlay?.addEventListener('click', closeDrawer);

  // ESC key closes drawer
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeDrawer();
  });

  // ── Badge Update ───────────────────────────────────────────────────────────
  function updateBadge(count) {
    document.querySelectorAll('.cart-badge, .mobile-cart-badge, .cart-drawer-count').forEach((el) => {
      el.textContent = count;
      el.style.display = count > 0 ? '' : 'none';
    });
  }

  // ── Refresh Drawer Content ─────────────────────────────────────────────────
  function refreshDrawer() {
    const itemsContainer = document.getElementById('cart-drawer-items');
    const emptyEl        = document.getElementById('cart-drawer-empty');
    const footerEl       = document.getElementById('cart-drawer-footer');
    if (!itemsContainer) return;

    fetch('/cart/json/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.json())
    .then(data => {
      if (!data.items || data.items.length === 0) {
        itemsContainer.innerHTML = '';
        emptyEl && (emptyEl.style.display = 'flex');
        footerEl && (footerEl.style.display = 'none');
        return;
      }
      emptyEl && (emptyEl.style.display = 'none');
      footerEl && (footerEl.style.display = '');
      itemsContainer.innerHTML = data.items.map(renderCartItem).join('');
      bindDrawerItemEvents();
      document.getElementById('cart-drawer-subtotal-amount').textContent =
        '₹' + data.total.toLocaleString('en-IN', { minimumFractionDigits: 0 });
      updateBadge(data.count);

      // Shipping note
      const noteEl = document.getElementById('cart-drawer-shipping-note');
      if (noteEl) {
        if (data.subtotal < 999) {
          noteEl.textContent = `Add ₹${(999 - data.subtotal).toFixed(0)} more for free shipping`;
          noteEl.style.color = 'var(--gold)';
        } else {
          noteEl.textContent = '✓ You qualify for free shipping!';
          noteEl.style.color = 'var(--success)';
        }
      }
    })
    .catch(() => {});
  }

  function renderCartItem(item) {
    return `
      <div class="cart-drawer-item" data-key="${item.key}">
        <img class="cart-drawer-img"
             src="${item.image || '/static/images/hero_fallback.jpg'}"
             alt="${item.name}" loading="lazy">
        <div class="cart-drawer-info">
          <div class="cart-drawer-item-name">${item.name}</div>
          <div class="cart-drawer-item-meta">${item.size ? 'Size: ' + item.size : ''}${item.color ? ' · ' + item.color : ''}</div>
          <div class="cart-drawer-item-price">₹${parseFloat(item.subtotal).toLocaleString('en-IN', { minimumFractionDigits: 0 })}</div>
          <div class="cart-drawer-qty">
            <button class="cart-drawer-qty-btn" data-key="${item.key}" data-action="decrease" aria-label="Decrease">−</button>
            <span class="cart-drawer-qty-val">${item.quantity}</span>
            <button class="cart-drawer-qty-btn" data-key="${item.key}" data-action="increase" aria-label="Increase">+</button>
          </div>
        </div>
        <button class="cart-drawer-remove" data-key="${item.key}" aria-label="Remove item">
          <i class="fa fa-times"></i>
        </button>
      </div>`;
  }

  function bindDrawerItemEvents() {
    // Quantity buttons
    document.querySelectorAll('.cart-drawer-qty-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const key    = btn.dataset.key;
        const action = btn.dataset.action;
        const row    = document.querySelector(`.cart-drawer-item[data-key="${key}"]`);
        const valEl  = row?.querySelector('.cart-drawer-qty-val');
        let qty      = parseInt(valEl?.textContent || '1', 10);
        qty = action === 'increase' ? qty + 1 : qty - 1;
        if (qty < 1) {
          removeFromCart(key);
          return;
        }
        updateCartItem(key, qty);
      });
    });

    // Remove buttons
    document.querySelectorAll('.cart-drawer-remove').forEach((btn) => {
      btn.addEventListener('click', () => removeFromCart(btn.dataset.key));
    });
  }

  function updateCartItem(key, quantity) {
    const fd = new FormData();
    fd.append('quantity', quantity);
    fd.append('csrfmiddlewaretoken', CSRF_TOKEN);
    fetch(`/cart/update/${encodeURIComponent(key)}/`, {
      method: 'POST', body: fd,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(() => refreshDrawer())
    .catch(() => {});
  }

  function removeFromCart(key) {
    const fd = new FormData();
    fd.append('csrfmiddlewaretoken', CSRF_TOKEN);
    fetch(`/cart/remove/${encodeURIComponent(key)}/`, {
      method: 'POST', body: fd,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(() => refreshDrawer())
    .catch(() => {});
  }

  // ── AJAX Add to Cart ───────────────────────────────────────────────────────
  document.addEventListener('submit', (e) => {
    const form = e.target.closest('.add-to-cart-form');
    if (!form) return;
    e.preventDefault();
    const btn = form.querySelector('[type=submit]');
    const origText = btn?.innerHTML;

    if (btn) {
      btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
      btn.disabled = true;
    }

    const fd = new FormData(form);
    fetch(form.action, {
      method: 'POST', body: fd,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        updateBadge(data.cart_count);
        openDrawer();
        if (btn) {
          btn.innerHTML = '<i class="fa fa-check"></i> Added!';
          setTimeout(() => {
            btn.innerHTML = origText;
            btn.disabled = false;
          }, 2000);
        }
      }
    })
    .catch(() => {
      if (btn) { btn.innerHTML = origText; btn.disabled = false; }
    });
  });

  // ── Wishlist Toggle (AJAX) ─────────────────────────────────────────────────
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-wishlist-toggle]');
    if (!btn) return;
    e.preventDefault();
    const productId = btn.dataset.wishlistToggle;
    const fd = new FormData();
    fd.append('csrfmiddlewaretoken', CSRF_TOKEN);
    fetch(`/wishlist/toggle/${productId}/`, {
      method: 'POST', body: fd,
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(r => r.json())
    .then(data => {
      const heart = btn.querySelector('i');
      if (heart) {
        heart.className = data.added ? 'fa fa-heart' : 'far fa-heart';
        btn.classList.toggle('active', data.added);
      }
      // Animate
      btn.classList.add('heart-animate');
      setTimeout(() => btn.classList.remove('heart-animate'), 400);
    })
    .catch(() => {});
  });

  // Expose for global use
  window.VornCart = { open: openDrawer, close: closeDrawer, refresh: refreshDrawer };
})();
