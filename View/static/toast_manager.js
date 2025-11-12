/** Toast Manager */
(function(){
  window.showToast = function(message, variant='primary', delay=2500){
    try {
      const container = document.getElementById('toastContainer') || document.body;
      const wrapper = document.createElement('div');
      wrapper.className = 'toast align-items-center text-bg-' + variant + ' border-0';
      wrapper.setAttribute('role','alert'); wrapper.setAttribute('aria-live','assertive'); wrapper.setAttribute('aria-atomic','true');
      wrapper.innerHTML = `
        <div class="d-flex">
          <div class="toast-body">${message}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>`;
      container.appendChild(wrapper);
      const t = new bootstrap.Toast(wrapper, { delay });
      t.show();
      wrapper.addEventListener('hidden.bs.toast', ()=> wrapper.remove());
    } catch(e) { console.warn('Toast error', e); }
  };
})();
