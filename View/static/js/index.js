
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
