// stripped module (to be unified later)
void 0;
// 基础表单验证：同步+异步占位，前后端双层验证预留
export const Validate = (function(){
  const patterns = {
    phone: /^\+?\d{6,15}$/,
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    ip: /^(?:\d{1,3}\.){3}\d{1,3}$/,
    url: /^(https?:\/\/).+/i,
  };
  function require(val){ return val!=null && String(val).trim().length>0; }
  function match(val, key){ const p = patterns[key]; return !p || p.test(String(val||'')); }
  function maxLen(val, n){ return String(val||'').length <= n; }
  async function serverCheck(path, payload){
    try{
      const res = await fetch(path, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload||{}) });
      const js = await res.json();
      return { ok: true, data: js };
    }catch(e){ return { ok:false, error: e } }
  }
  return { require, match, maxLen, serverCheck };
})();
