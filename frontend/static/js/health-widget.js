// stripped module (to be unified later)
void 0;
// Reusable health indicator and card module
// Usage:
//  - initGlobalIndicator({ el, pollingMs })
//  - initHealthCard({ el, pollingMs })

export function fetchHealth(timeoutMs = 2500) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), timeoutMs);
  return fetch('/health', { signal: ctrl.signal })
    .finally(() => clearTimeout(id))
    .then(r => r.json())
    .catch(e => ({ code: 1, error: String(e) }));
}

export function initGlobalIndicator({ el, pollingMs = 5000, onUpdate } = {}) {
  // Auto create dot/text inside host if not provided
  if (!el) return () => {};
  const dot = el.querySelector('[data-dot]') || (() => {
    const s = document.createElement('span'); s.setAttribute('data-dot',''); s.style.cssText = 'width:10px;height:10px;border-radius:999px;background:#9ca3af;display:inline-block;margin-right:6px'; el.appendChild(s); return s;
  })();
  const txt = el.querySelector('[data-text]') || (() => {
    const s = document.createElement('span'); s.setAttribute('data-text',''); s.style.cssText = 'font-size:12px;'; el.appendChild(s); return s;
  })();
  async function refresh() {
    try {
      const j = await fetchHealth();
      const d = j.data || {};
      const ap = d.ai_probe || {};
      const ok = d.status === 'ok';
      const reach = ap.reachable === true;
      const color = ok ? (reach ? '#16a34a' : '#f59e0b') : '#ef4444'; // green/amber/red
      dot.style.background = color;
      txt.textContent = (ok && reach) ? `正常 · ${ap.latency_avg_ms ?? ap.latency_ms ?? '-' }ms` : (ok ? 'AI未连接' : '异常');
      if (typeof onUpdate === 'function') onUpdate(d);
    } catch (_) {
      dot.style.background = '#ef4444';
      txt.textContent = '异常';
    }
  }
  refresh();
  const timer = setInterval(refresh, pollingMs);
  return () => clearInterval(timer);
}

export function initHealthCard({ el, pollingMs = 5000 } = {}) {
  if (!el) return () => {};
  el.innerHTML = `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <span data-dot style="width:10px;height:10px;border-radius:999px;background:#9ca3af;display:inline-block"></span>
      <strong data-status style="font-size:12px;color:#111827">—</strong>
      <span data-ai style="font-size:12px;">AI: —</span>
      <button data-refresh class="btn" style="margin-left:auto">刷新</button>
    </div>
    <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-bottom:8px">
      <div style="font-size:12px">延迟(ms)：<span data-latency>—</span></div>
      <div style="font-size:12px">平均(ms)：<span data-avg>—</span></div>
      <div style="font-size:12px">样本数：<span data-samples>0</span></div>
      <div style="font-size:12px">模型端口：<span data-ai-hostport>—</span></div>
    </div>
    <canvas data-chart width="280" height="80" style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:6px"></canvas>
  `;
  const $ = sel => el.querySelector(sel);
  const dot = $('[data-dot]');
  const statusEl = $('[data-status]');
  const aiEl = $('[data-ai]');
  const latencyEl = $('[data-latency]');
  const avgEl = $('[data-avg]');
  const samplesEl = $('[data-samples]');
  const hostPortEl = $('[data-ai-hostport]');
  const refreshBtn = $('[data-refresh]');
  const canvas = $('[data-chart]');
  const ctx = canvas.getContext('2d');
  const history = []; // store last 30 latencies

  function percentile(arr, p){
    if(!arr.length) return 0; const a = [...arr].sort((x,y)=>x-y);
    const idx = Math.min(a.length-1, Math.max(0, Math.round(p*(a.length-1))));
    return a[idx];
  }
  function drawChart() {
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0,0,w,h);
    // axes
    ctx.strokeStyle = '#e5e7eb'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(30,10); ctx.lineTo(30,h-20); ctx.lineTo(w-10,h-20); ctx.stroke();
    if (history.length < 2) return;
    const max = Math.max(...history, 1);
    const min = Math.min(...history, 0);
    const avg = history.reduce((s,v)=>s+v,0)/history.length;
    const p98 = percentile(history, 0.98);
    const padL = 30, padB = 20;
    const plotW = w - padL - 10, plotH = h - 10 - padB;
    ctx.strokeStyle = '#2563eb'; ctx.lineWidth = 2; ctx.beginPath();
    history.forEach((v, i) => {
      const x = padL + (i/(history.length-1)) * plotW;
      const y = 10 + (1 - (v - min) / Math.max(max-min,1)) * plotH;
      if (i === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    });
    ctx.stroke();
    // avg line
    const yAvg = 10 + (1 - (avg - min) / Math.max(max-min,1)) * plotH;
    ctx.strokeStyle = '#64748b'; ctx.setLineDash([4,4]); ctx.beginPath(); ctx.moveTo(padL, yAvg); ctx.lineTo(w-10, yAvg); ctx.stroke();
    // p98 line
    const yP98 = 10 + (1 - (p98 - min) / Math.max(max-min,1)) * plotH;
    ctx.strokeStyle = '#f97316'; ctx.setLineDash([2,4]); ctx.beginPath(); ctx.moveTo(padL, yP98); ctx.lineTo(w-10, yP98); ctx.stroke();
    ctx.setLineDash([]);
    // labels
    ctx.fillStyle = '#64748b'; ctx.font = '10px sans-serif'; ctx.fillText(`avg:${avg.toFixed(1)}ms`, w-90, yAvg-4);
    ctx.fillStyle = '#f97316'; ctx.fillText(`p98:${p98.toFixed(1)}ms`, w-90, yP98-4);
  }

  async function refresh() {
    try {
      const j = await fetchHealth();
      const d = j.data || {};
      const ap = d.ai_probe || {};
      const ok = d.status === 'ok';
      const reach = ap.reachable === true;
      const color = ok ? (reach ? '#16a34a' : '#f59e0b') : '#ef4444';
      dot.style.background = color;
      statusEl.textContent = ok ? 'ok' : 'error';
      aiEl.textContent = `AI: ${reach ? '连接' : '未连'}`;
      aiEl.style.color = reach ? '#16a34a' : '#f59e0b';
      latencyEl.textContent = ap.latency_ms ?? '-';
      avgEl.textContent = ap.latency_avg_ms ?? '-';
      samplesEl.textContent = ap.samples ?? 0;
      hostPortEl.textContent = `${ap.host ?? '-'}:${ap.port ?? '-'}`;
      if (typeof ap.latency_ms === 'number') {
        history.push(ap.latency_ms);
        if (history.length > 30) history.shift();
      }
      drawChart();
    } catch (_) {
      dot.style.background = '#ef4444';
      statusEl.textContent = 'error';
      aiEl.textContent = 'AI: 未连';
      aiEl.style.color = '#ef4444';
    }
  }

  refresh();
  const timer = setInterval(refresh, pollingMs);
  refreshBtn.addEventListener('click', refresh);
  return () => clearInterval(timer);
}
