// Auto-refresh specific pages every AP_SHARED.autoRefreshMs milliseconds (default 10s)
(function(){
  const ms = (window.AP_SHARED && window.AP_SHARED.autoRefreshMs) || 10000;
  // Only enable when running dev server or explicitly allowed
  const isDevOrigin = /localhost|127\.0\.0\.1/.test(location.hostname);
  if (!isDevOrigin) return;
  const allow = new Set([
    '/pages/api-doc.html',
    '/pages/api-map.html',
    '/pages/run.html',
    '/pages/ai-demo.html',
    '/pages/login.html',
    '/pages/index.html',
    '/pages/visual_pipeline.html',
    '/pages/monitor.html',
    '/pages/rbac.html'
  ]);
  // Normalize pathname to .html form
  function normalizePath(p){
    if (p.endsWith('.html')) return p;
    // Map path without .html to .html
    const name = p.replace(/\/$/, '').split('/').pop();
    if (!name) return p;
    return `/pages/${name}.html`;
  }
  const path = normalizePath(location.pathname);
  if (!allow.has(path)) return;
  // If livereload is present, it will trigger on file change; this timer is a fallback
  try {
    setInterval(()=>{ try{ location.reload(); }catch(e){ console.warn('[autorefresh] reload failed', e); } }, ms);
    console.log('[autorefresh] enabled for', path, 'interval', ms);
  } catch (e) {
    console.warn('[autorefresh] failed to enable', e);
  }
})();
const pagesToReload = [
    '/pages/index.html',
    '/pages/run.html',
    '/pages/monitor.html',
    '/pages/api-doc.html',
    '/pages/visual_pipeline.html',
    '/pages/login.html',
    '/pages/ai-demo.html',
    '/pages/api-map.html',
    '/pages/rbac.html'
];

setInterval(() => {
    pagesToReload.forEach(page => {
        fetch(page, { method: 'HEAD' })
            .then(response => {
                if (!response.ok) {
                    console.warn(`Page ${page} is not accessible.`);
                }
            })
            .catch(err => console.error(`Error checking page ${page}:`, err));
    });
}, 30000); // 每30秒检查一次页面状态
