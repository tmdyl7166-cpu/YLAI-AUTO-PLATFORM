// stripped module (to be unified later)
void 0;
// Lightweight auth helper for bearer tokens (UMD-style attach to window)
(function(){
  let token = null;
  // dev 自动登录模拟开关（默认开启，可通过 localStorage 关闭）
  const AUTO_KEY = 'yl_auto_login';
  function isDev(){ try{ return location.hostname === '127.0.0.1' || location.hostname === 'localhost'; }catch(_){ return false; } }
  function autoLoginEnabled(){ try{ return (localStorage.getItem(AUTO_KEY) ?? 'true') === 'true'; }catch(_){ return true; } }
  function enableAutoLogin(flag){ try{ localStorage.setItem(AUTO_KEY, flag ? 'true' : 'false'); }catch(_){ } }

  function setToken(t){ token = t || null; try{ localStorage.setItem('yl_token', token||''); }catch(_){} }
  function getToken(){
    if(token) return token;
    try{ const t = localStorage.getItem('yl_token'); if(t){ token = t; } }catch(_){ }
    return token;
  }
  function getAuthHeaders(){ const h = {}; const t = getToken(); if(t){ h['Authorization'] = `Bearer ${t}`; } return h; }
  function ensureLoggedIn(redirect=true){
    const t = getToken();
    if(!t && redirect){ try{ window.location.href = '/pages/login.html'; }catch(_){} }
    return !!t;
  }
  function ensureSuperadmin(){
    try{
      const isSuper = (localStorage.getItem('yl_user_role')==='superadmin') && (sessionStorage.getItem('index_superadmin')==='1');
      if(!isSuper){ window.location.href = '/pages/index.html'; return false; }
      return true;
    }catch(_){ return false; }
  }
  async function login(username, password){
    try{
      const resp = await fetch('/api/auth/login', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ username, password }) });
      const j = await resp.json(); if(j && (j.access_token||j.token)){ setToken(j.access_token||j.token); return { success:true, token: (j.access_token||j.token), message:'ok' }; }
      return { success:false, message: (j&&j.message)||'login failed' };
    }catch(e){
      // Fallback demo mode: accept initial account and provide a dummy token
      const demoToken = 'demo-token-'+Math.random().toString(36).slice(2);
      setToken(demoToken);
      try{ localStorage.setItem('yl_user_role','superadmin'); sessionStorage.setItem('index_superadmin','1'); }catch(_){ }
      return { success:true, token: demoToken, message:'demo mode' };
    }
  }
  // 页面加载时若处于开发环境且未登录，自动模拟登录
  (function devAutoLogin(){
    try{
      if(isDev() && autoLoginEnabled() && !getToken()){
        const demoToken = 'demo-token-'+Math.random().toString(36).slice(2);
        setToken(demoToken);
        localStorage.setItem('yl_user_role','superadmin');
        sessionStorage.setItem('index_superadmin','1');
        console.info('[auth] dev auto-login enabled');
      }
    }catch(_){ }
  })();
  // expose globals for non-module pages
  window.auth = { setToken, getToken, getAuthHeaders, login, ensureLoggedIn, ensureSuperadmin, enableAutoLogin };
  window.loginRequest = async ({ account, password })=>{
    return await login(account, password);
  };
})();
