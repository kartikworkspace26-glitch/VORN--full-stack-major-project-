/**
 * VORN — Page Loader
 * Luxury brand-style loading screen that fades out once page is ready.
 */
(function () {
  'use strict';

  const loader = document.getElementById('page-loader');
  if (!loader) return;

  function hideLoader() {
    loader.classList.add('loaded');
    setTimeout(() => loader.remove(), 700);
  }

  // Hide after fonts + critical resources are ready
  if (document.readyState === 'complete') {
    setTimeout(hideLoader, 400);
  } else {
    window.addEventListener('load', () => setTimeout(hideLoader, 400));
    // Safety fallback — never block UX for more than 3s
    setTimeout(hideLoader, 3000);
  }
})();
