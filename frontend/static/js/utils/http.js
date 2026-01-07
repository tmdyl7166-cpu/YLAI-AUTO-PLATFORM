// stripped module (to be unified later)
void 0;
// 统一 HTTP 封装：版本戳、防缓存、CORS 友好、JSON/FormData 自动
export const Http = (function(){
  const version = (typeof window !== 'undefined' && window.IndexConfig && window.IndexConfig.VERSION) || 'v0';
  let etagCache = new Map();
  function withVersion(url){
    try{
      const u = new URL(url, window.location.origin);
      u.searchParams.set('_v', version);
      return u.toString().replace(window.location.origin,'');
    }catch(_){
      const sep = url.includes('?') ? '&' : '?';
      return url + sep + '_v=' + encodeURIComponent(version);
    }
  }
  async function request(path, { method='GET', headers={}, body=null }={}){
    const isForm = (body && typeof FormData !== 'undefined' && body instanceof FormData);
    const opts = { method, headers: { 'Cache-Control':'no-store', ...headers } };
    if (method === 'POST' || method === 'PUT' || method === 'PATCH'){
      if (isForm){
        opts.body = body;
      } else if (body != null){
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
      }
    }
    const url = withVersion(path);
    // ETag conditional
    const prevEtag = etagCache.get(url);
    if (prevEtag){ opts.headers['If-None-Match'] = prevEtag; }
    const res = await fetch(url, opts);
    const ct = (res.headers.get('content-type')||'').toLowerCase();
    const etag = res.headers.get('etag'); if(etag){ etagCache.set(url, etag); }
    if (res.status === 304){ return { ok: true, status: 304, data: null }; }
    const data = ct.includes('application/json') ? await res.json() : await res.text();
    return { ok: res.ok, status: res.status, data };
  }
  return { request, withVersion };
})();
