const API_BASE = window.API_TARGET || '';

export async function apiGet(path) {
  const resp = await fetch(`${API_BASE}${path}`, { credentials: 'include' });
  return resp;
}

export async function apiPost(path, body) {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
    credentials: 'include'
  });
  return resp;
}

export function wsConnect(path) {
  const url = (API_BASE || '').replace('http', 'ws') + path;
  return new WebSocket(url);
}

export async function generateText(prompt) {
  const r = await apiPost('/api/generate', { prompt });
  return r.ok ? r.text() : Promise.reject(new Error(`HTTP ${r.status}`));
}
