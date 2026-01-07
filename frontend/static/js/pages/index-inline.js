// stripped page controller
void 0;
// Index page external inline: reload WS + small helpers
(function(){
  function connectReloadWS(){
    try{
      const proto = (location.protocol==='https:'?'wss':'ws');
      const ws = new WebSocket(proto+'://'+location.host+'/ws/monitor');
      ws.onmessage = function(e){ try{ const msg = JSON.parse(e.data); if(msg && msg.type==='reload'){ window.location.reload(); } }catch(_){} };
      ws.onclose = function(){ setTimeout(connectReloadWS, 2000); };
    }catch(_){ setTimeout(connectReloadWS, 2000); }
  }
  connectReloadWS();
})();
// Deprecated: use /static/js/pages/index.js
(function(){
  try { console.warn('[deprecated] index-inline.js is not used anymore.'); } catch {}
})();
