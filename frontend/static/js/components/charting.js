// stripped module (to be unified later)
void 0;
// Charting helper: load local Chart.js and render common charts

export async function ensureChartLib() {
  if (window.Chart) return;
  const localUrl = '/static/vendor/chart.min.js';
  const cdnUrl = 'https://cdn.jsdelivr.net/npm/chart.js';
  async function load(src){
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src; s.onload = resolve; s.onerror = reject; document.head.appendChild(s);
    });
  }
  try { await load(localUrl); }
  catch(_) { await load(cdnUrl); }
}

export async function renderCpuLine(el, data = [20,35,28,42,33], labels = ['1','2','3','4','5']) {
  await ensureChartLib();
  const ctx = document.createElement('canvas'); el.innerHTML=''; el.appendChild(ctx);
  return new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: [{ label: 'CPU %', data, borderColor: '#1df0ff' }] },
    options: { responsive: true, maintainAspectRatio: false }
  });
}

export async function renderModuleDonut(el, data = [40,25,20,15], labels = ['采集','识别','AI','其他']) {
  await ensureChartLib();
  const ctx = document.createElement('canvas'); el.innerHTML=''; el.appendChild(ctx);
  return new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ data, backgroundColor: ['#2563eb','#10b981','#f59e0b','#64748b'] }] },
    options: { responsive: true, maintainAspectRatio: false }
  });
}
