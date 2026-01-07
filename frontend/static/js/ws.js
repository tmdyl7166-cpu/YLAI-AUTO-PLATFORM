// stripped module (to be unified later)
void 0;
(function(global){
  function connectPipelineWS(taskId, handlers){
    handlers = handlers || {};
    var proto = location.protocol === 'https:' ? 'wss' : 'ws';
    var url = proto + '://' + location.host + '/ws/pipeline/' + encodeURIComponent(taskId);
    var ws = new WebSocket(url);
    ws.onopen = function(){ handlers.onOpen && handlers.onOpen(); };
    ws.onclose = function(){ handlers.onClose && handlers.onClose(); };
    ws.onerror = function(e){ handlers.onError && handlers.onError(e); };
    ws.onmessage = function(ev){
      try{ var data = JSON.parse(ev.data); handlers.onMessage && handlers.onMessage(data); }
      catch(_){ handlers.onMessage && handlers.onMessage(ev.data); }
    };
    return ws;
  }
  global.WS = global.WS || {}; 
  global.WS.connectPipelineWS = connectPipelineWS;
})(window);
