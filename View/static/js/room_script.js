
const socket = io();

document.getElementById('copyRoomCode').addEventListener('click', () => {
  const code = document.getElementById('roomCode').textContent;
  navigator.clipboard.writeText(code);
  createToast('Room code copied!', 'info');
});

document.getElementById('toggleThemeBtn').addEventListener('click', function() {
  const htmlEl = document.documentElement;
  const currentTheme = htmlEl.getAttribute('data-bs-theme');
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  htmlEl.setAttribute('data-bs-theme', newTheme);
  this.textContent = newTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
  localStorage.setItem('theme', newTheme);
});

window.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    document.getElementById('toggleThemeBtn').textContent = savedTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
  }
});

function createToast(message, type='info') {
  const toastContainer = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-bg-${type} border-0 show mb-2`;
  toast.role = 'alert';
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
