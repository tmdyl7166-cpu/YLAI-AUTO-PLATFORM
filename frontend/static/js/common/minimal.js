// Unified minimal functionality for all pages: render a badge, verify CSS/JS pointers, and log health
(function(){
  try {
    const badge = document.createElement('div');
    badge.style = 'position:fixed;bottom:12px;right:12px;z-index:9999;padding:6px 10px;border-radius:999px;background:#0a0f1e;color:#1de9b6;border:1px solid rgba(29,240,255,0.35);font-size:12px;';
    const ver = (document.querySelector('link[rel="modulepreload"]')?.href || '').split('v=')[1] || 'dev';
    badge.textContent = `公共模块: OK · v=${ver}`;
    document.body.appendChild(badge);
  } catch (e) {
    console.error('[common:minimal] badge error', e);
  }

  function checkResource(url){
    return fetch(url, { method: 'HEAD' }).then(r=>({ url, ok: r.ok, status: r.status })).catch(err=>({ url, ok:false, error:String(err) }));
  }

  (async ()=>{
    try {
      const cssLinks = Array.from(document.querySelectorAll('link[rel="stylesheet"], link[rel="preload"][as="style"]')).map(l=> l.href).filter(Boolean);
      const jsLinks = Array.from(document.querySelectorAll('script[type="module"]')).map(s=> s.src).filter(Boolean);
      const targets = [...new Set([...cssLinks, ...jsLinks])];
      const results = await Promise.all(targets.map(checkResource));
      const missing = results.filter(r=> !r.ok);
      if(missing.length){
        console.warn('[common:minimal] 资源检查失败:', missing);
      } else {
        console.log('[common:minimal] 资源检查通过:', results.length);
      }
    } catch (e) {
      console.warn('[common:minimal] 资源检查异常', e);
    }
  })();

  // Ensure pages are visible: remove common hidden classes and force opacity/display
  function revealAll(){
    try {
      const body = document.body;
      if(body){ body.style.opacity = '1'; body.style.display = ''; }
      const hiddenClasses = ['hidden','page-fade-in'];
      hiddenClasses.forEach(cls=>{
        document.querySelectorAll('.'+cls).forEach(el=> el.classList.remove(cls));
      });
      // Force main containers to be visible
      ['#index-root','#run-root','#monitor-root','#ai-demo-root'].forEach(sel=>{
        const el = document.querySelector(sel);
        if(el){ el.style.opacity = '1'; el.style.display = ''; }
      });
    } catch (e) {
      console.warn('[common:minimal] reveal error', e);
    }
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', revealAll);
  } else {
    revealAll();
  }
})();
