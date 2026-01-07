// Simple theme controller: toggles light/dark and persists
const KEY = 'ylai-theme';
export function applyTheme(theme) {
  const t = theme || localStorage.getItem(KEY) || 'light';
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem(KEY, t);
}
export function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  applyTheme(next);
}
export function initThemeUI(buttonId = 'theme-toggle') {
  applyTheme();
  const btn = document.getElementById(buttonId);
  if (btn) {
    btn.addEventListener('click', toggleTheme);
  }
}
