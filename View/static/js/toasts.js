(function(){
  const toastContainerId = 'toastContainer';
  function ensureContainer(){
    let el = document.getElementById(toastContainerId);
    if (!el) {
      el = document.createElement('div');
      el.id = toastContainerId;
      el.className = 'toast-container position-fixed top-0 end-0 p-3';
      document.body.appendChild(el);
    }
    return el;
  }
  function showToast(title, body, variant='primary'){
    const container = ensureContainer();
    const wrapper = document.createElement('div');
    wrapper.className = 'toast align-items-center border-0';
    wrapper.role = 'alert';
    wrapper.ariaLive = 'assertive';
    wrapper.ariaAtomic = 'true';
    wrapper.innerHTML = `
      <div class="toast-header bg-${variant} text-white">
        <strong class="me-auto">${title}</strong>
        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body">${body}</div>`;
    container.appendChild(wrapper);
    const t = new bootstrap.Toast(wrapper, { delay: 2500 });
    t.show();
    wrapper.addEventListener('hidden.bs.toast', () => wrapper.remove());
  }
  window.TODToast = { show: showToast };
})();
