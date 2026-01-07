// Renders API mapping from markdown-derived JSONs into collapsible lists
import { initThemeUI } from '/static/js/core/theme.js';
initThemeUI('theme-toggle');

async function loadJSON(url) {
  try { return await (await fetch(url)).json(); } catch { return null; }
}

async function main() {
  const root = document.getElementById('api-map-root');
  if (!root) return;
  // Minimal clickable module placeholder guard
  if (!root.children.length) {
    const section = document.createElement('section');
    section.className = 'card';
    const btn = document.createElement('button');
    btn.className = 'btn';
    btn.textContent = '加载 API 映射';
    btn.onclick = ()=> alert('API 映射占位（后续由模块渲染）');
    section.appendChild(btn);
    root.appendChild(section);
  }
  const moduleStatus = await loadJSON('/pages/data/module-status.json') || {};
  const routeStatus = await loadJSON('/pages/data/module-routes-status.json') || {};
  const modules = Object.keys(moduleStatus);

  const container = document.createElement('div');
  container.className = 'cards';

  modules.forEach(id => {
    const status = moduleStatus[id] || '🔴';
    const routes = routeStatus[id] || [];
    const card = document.createElement('section');
    card.className = 'card';
    const title = document.createElement('h3');
    title.textContent = `${id} ${status}`;
    card.appendChild(title);

    const list = document.createElement('ul');
    routes.forEach(r => {
      const li = document.createElement('li');
      li.textContent = `${r.method} ${r.path} · ${r.status || '🔴'} · ${r.chapter || ''}`;
      list.appendChild(li);
    });
    card.appendChild(list);
    container.appendChild(card);
  });

  root.innerHTML = '';
  root.appendChild(container);
}

main();
