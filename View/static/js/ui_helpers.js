// View/static/js/ui_helpers.js
export const qs = (selector, scope = document) => scope.querySelector(selector);
export const qsa = (selector, scope = document) => [...scope.querySelectorAll(selector)];

export function show(el) {
  el.classList.remove('hidden');
}

export function hide(el) {
  el.classList.add('hidden');
}

export function updateText(id, text) {
  const el = qs(id);
  if (el) el.textContent = text;
}
