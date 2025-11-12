(() => {
  // Theme toggle persists in localStorage
  const btn = document.getElementById('themeToggle');
  if (btn) {
    const apply = (mode) => document.documentElement.setAttribute('data-bs-theme', mode);
    const stored = localStorage.getItem('theme') || 'auto';
    if (stored !== 'auto') apply(stored);

    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-bs-theme') || 'auto';
      const next = current === 'light' ? 'dark' : (current === 'dark' ? 'auto' : 'light');
      localStorage.setItem('theme', next);
      if (next === 'auto') document.documentElement.removeAttribute('data-bs-theme');
      else apply(next);
    });
  }
})();

// Toast helper
window.showToast = (title, body, delay=3000) => {
  const cont = document.getElementById('toastContainer');
  if (!cont) return;
  const el = document.createElement('div');
  el.className = 'toast align-items-center text-bg-dark border-0';
  el.role = 'alert'; el.ariaLive = 'assertive'; el.ariaAtomic = 'true';
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <strong>${title}</strong><div class="small opacity-75">${body||''}</div>
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>`;
  cont.appendChild(el);
  const toast = new bootstrap.Toast(el, { delay });
  toast.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
};
