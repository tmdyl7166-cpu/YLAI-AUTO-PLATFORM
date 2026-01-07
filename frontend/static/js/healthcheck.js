// stripped module (to be unified later)
void 0;
// 可视化健康检查条：资源加载与 API 连接状态
(function(){
  try{
    var cfg = {
      autoHide: (localStorage.getItem('yl_dbg_autoHide') ?? 'true') === 'true',
      wsBubbleEnabled: (localStorage.getItem('yl_dbg_wsBubble') ?? 'true') === 'true',
      snapshotEnabled: (localStorage.getItem('yl_dbg_snapshot') ?? 'true') === 'true'
    };
    var bar = document.createElement('div');
    bar.id = 'yl-healthcheck-bar';
    bar.style = 'position:fixed;top:0;left:0;right:0;height:24px;display:flex;align-items:center;gap:10px;padding:0 10px;background:rgba(37,99,235,.10);border-bottom:1px solid #e5e7eb;font-size:12px;color:#111827;z-index:9999;backdrop-filter:saturate(150%) blur(6px)';
    bar.innerHTML = '<span>Health</span><span id="hc-static">static: -</span><span id="hc-api">api: -</span><span id="hc-mod">modules: -</span><span id="hc-bus">bus: -</span><span id="hc-cfg">cfg: -</span><button id="hc-toggle" style="margin-left:auto;background:transparent;border:1px solid #cbd5e1;border-radius:6px;padding:2px 8px;cursor:pointer;color:#374151">隐藏</button>';
    document.body.appendChild(bar);
    // 检查静态资源（modules.js）加载
    var staticEl = document.getElementById('hc-static');
    var cfgEl = document.getElementById('hc-cfg');
    if(staticEl){ staticEl.textContent = 'static: loading'; }
    import('/static/js/modules.js').then(function(mod){
      if(staticEl){ staticEl.textContent = 'static: ok'; staticEl.style.color = '#16b777'; }
      if(cfgEl){ cfgEl.textContent = 'cfg: AH:'+(cfg.autoHide?'Y':'N')+' WS:'+(cfg.wsBubbleEnabled?'Y':'N')+' SS:'+(cfg.snapshotEnabled?'Y':'N'); cfgEl.style.color = '#6b7280'; }
      // 版本打印（一次）
      try{ mod.printVersion && mod.printVersion(); }catch(_){ }
    }).catch(function(){ if(staticEl){ staticEl.textContent = 'static: fail'; staticEl.style.color = '#ef4444'; } });
    // 检查 API 连接（/api/status）
    var apiEl = document.getElementById('hc-api');
    if(apiEl){ apiEl.textContent = 'api: probing'; }
    var t0 = (typeof performance!=='undefined' && performance.now) ? performance.now() : Date.now();
    fetch('/api/status',{ method:'GET' }).then(function(r){
      var t1 = (typeof performance!=='undefined' && performance.now) ? performance.now() : Date.now();
      var rtt = Math.max(0, Math.round((t1 - t0)));
      if(!apiEl) return; if(r.ok){ apiEl.textContent = 'api: ok '+rtt+'ms'; apiEl.style.color = '#16b777'; }
      else { apiEl.textContent = 'api: http '+r.status+' '+rtt+'ms'; apiEl.style.color = '#f59e0b'; }
    }).catch(function(e){ if(apiEl){ apiEl.textContent = 'api: fail'; apiEl.style.color = '#ef4444'; } });
    // /api/modules RTT
    var modEl = document.getElementById('hc-mod');
    if(modEl){ modEl.textContent = 'modules: probing'; }
    var m0 = (typeof performance!=='undefined' && performance.now) ? performance.now() : Date.now();
    fetch('/api/modules',{ method:'GET' }).then(function(r){
      var m1 = (typeof performance!=='undefined' && performance.now) ? performance.now() : Date.now();
      var mrtt = Math.max(0, Math.round((m1 - m0)));
      if(!modEl) return; if(r.ok){ modEl.textContent = 'modules: ok '+mrtt+'ms'; modEl.style.color = '#16b777'; }
      else { modEl.textContent = 'modules: http '+r.status+' '+mrtt+'ms'; modEl.style.color = '#f59e0b'; }
    }).catch(function(){ if(modEl){ modEl.textContent = 'modules: fail'; modEl.style.color = '#ef4444'; } });

    // 事件总线心跳（modules:invoke）
    var busEl = document.getElementById('hc-bus');
    var count = 0; function updateBus(){ if(busEl){ busEl.textContent = 'bus: '+count; busEl.style.color = count>0 ? '#16b777' : '#6b7280'; } }
    window.addEventListener('modules:invoke', function(){ count++; updateBus(); }, { passive:true });
    setInterval(updateBus, 3000);

    // 一键隐藏/收起控件（生产环境可用）
    var toggleBtn = document.getElementById('hc-toggle');
    if(toggleBtn){
      toggleBtn.addEventListener('click', function(){
        var hidden = bar.getAttribute('data-hidden') === '1';
        if(hidden){ bar.style.transform = 'translateY(0)'; bar.setAttribute('data-hidden','0'); toggleBtn.textContent = '隐藏'; }
        else { bar.style.transform = 'translateY(-100%)'; bar.setAttribute('data-hidden','1'); toggleBtn.textContent = '显示'; }
      });
    }

    // 自动隐藏（所有项正常时）
    function allGreen(){
      var s = document.getElementById('hc-static');
      var a = document.getElementById('hc-api');
      var m = document.getElementById('hc-mod');
      return s && a && m && /ok/.test(s.textContent) && /ok/.test(a.textContent) && /ok/.test(m.textContent);
    }
    if(cfg.autoHide){
      setTimeout(function(){ if(allGreen()){ bar.style.transform = 'translateY(-100%)'; bar.setAttribute('data-hidden','1'); var t=document.getElementById('hc-toggle'); if(t) t.textContent='显示'; } }, 5000);
    }
  }catch(_){ /* ignore */ }
})();
