// stripped page controller
void 0;
(async function(){
  // Ensure containers and render base UI (topbar + layout skeleton)
  function ensureContainers(){
    if(!document.getElementById('topbar')){ const h=document.createElement('header'); h.id='topbar'; document.body.prepend(h); }
    if(!document.getElementById('monitor-root')){ const m=document.createElement('main'); m.id='monitor-root'; document.body.appendChild(m); }
  }
    // Minimal clickable module placeholder guard
    (function ensureMinimal(){
      const root = document.getElementById('monitor-root');
      if (root && !root.children.length) {
        const section = document.createElement('section');
        section.className = 'card';
        const btn = document.createElement('button');
        btn.className = 'btn';
        btn.textContent = '打开监控面板';
        btn.onclick = ()=> alert('监控面板占位（后续由模块渲染）');
        section.appendChild(btn);
        root.appendChild(section);
      }
    })();
  function renderTopbar(){
    // 仅确保占位容器存在，实际导航由 common/topbar.js 统一渲染
    if(!document.getElementById('topbar')){
      const h=document.createElement('header'); h.id='topbar'; document.body.prepend(h);
    }
  }
  function renderLayout(){
    const root=document.getElementById('monitor-root'); if(!root) return;
    root.innerHTML = `
      <div id="global-health-indicator" style="margin:8px 0"></div>
      <main class="container">
        <section class="card" style="flex:1">
          <h2>AI 优化建议</h2>
          <textarea id="aiErrorInputMon" placeholder="粘贴终端错误或日志片段"></textarea>
          <div style="display:flex;gap:8px">
            <button id="aiOptimizeSubmitMon">提交到 AI</button>
            <button id="aiOptimizeClearMon">清空</button>
          </div>
          <pre id="aiOptimizeResultMon" style="height:180px"></pre>
        </section>
        <section class="card scrollable" style="flex:2">
          <h2>模块监控</h2>
          <div id="monitor-modules" class="module-grid"></div>
          <div id="monitor-status" style="margin-top:12px"></div>
        </section>
        <section class="card scrollable" style="flex:2">
          <h2>日志</h2>
          <input id="logFilter" type="text" placeholder="过滤日志..." style="width:100%;margin-bottom:6px" />
          <pre id="logBox" style="height:180px"></pre>
        </section>
        <section class="card scrollable" style="flex:1">
          <h2>已执行脚本</h2>
          <ul id="executedScripts"></ul>
        </section>
      </main>
      <section class="card" style="margin:16px 0">
        <h2>占位面板</h2>
        <div id="monitor-ph" style="min-height:40px"></div>
        <div style="display:flex;gap:8px;margin-top:8px">
          <button data-ph="status">状态</button>
          <button data-ph="config">配置</button>
          <button data-ph="logs">日志</button>
        </div>
      </section>`;
  }

  // 优先通过 modules/registry 进行统一挂载
  try {
    const { mountModule } = await import('../modules/registry.js?v=__ASSET_VERSION__');
    await mountModule('monitor', 'monitor-root');
  } catch (e) {
    // 回退到现有渲染逻辑
    ensureContainers();
    renderTopbar();
    renderLayout();
  }
  // auth helper
  const authMod = await import('/static/js/auth.js').catch(()=>({auth:{getAuthHeaders:()=>({}), login:async()=>({})}}));
  const { auth } = authMod;
  // 取消登录限制：不再强制跳转登录页
  // 注入右上角登录状态徽标（纯 JS，不改 HTML）
  (function injectAuthBadge(){ try{ const role = localStorage.getItem('yl_user_role') || 'user'; const wrap=document.createElement('div'); wrap.style.position='fixed'; wrap.style.top='14px'; wrap.style.right='14px'; wrap.style.zIndex='9999'; wrap.style.display='flex'; wrap.style.gap='8px'; const badge=document.createElement('div'); badge.style.padding='6px 10px'; badge.style.borderRadius='999px'; badge.style.fontSize='12px'; badge.style.background='#0a0f1e'; badge.style.color='#1de9b6'; badge.style.border='1px solid rgba(29,240,255,0.35)'; const acc = (auth.getUser?.() && auth.getUser().account) || ''; badge.textContent = `已登录：${acc||'用户'}｜角色：${role}`; const exit=document.createElement('button'); exit.textContent='退出登录'; exit.className='btn'; exit.style.padding='6px 10px'; exit.style.borderRadius='999px'; exit.style.background='#ef4444'; exit.style.color='#fff'; exit.style.border='none'; exit.style.cursor='pointer'; exit.onclick=()=>{ try{ (auth.clearToken?.()||auth.setToken?.('')); }catch(_){ } try{ localStorage.removeItem('yl_user_role'); }catch(_){ } window.location.href='/pages/login.html'; }; wrap.appendChild(badge); wrap.appendChild(exit); document.body.appendChild(wrap);}catch(_){ } })();
  // Health widgets
  try{
    const modHW = await import('/static/js/health-widget.js');
    const host = document.getElementById('global-health-indicator');
    if(host && typeof modHW.initGlobalIndicator === 'function'){
      modHW.initGlobalIndicator({ el: host, pollingMs: 5000 });
    }
    const cardHost = document.getElementById('health-card-host');
    if(cardHost && typeof modHW.initHealthCard === 'function'){
      modHW.initHealthCard({ el: cardHost });
    }
  }catch(_){ }

  // Shared modules
  const mod = await import('/static/js/modules.js').catch(()=>({}));
  const apiModules = mod.apiModules || (async()=>[]);
  const apiStatus = mod.apiStatus || (async()=>({}));
  const bindQuickActions = mod.bindQuickActions || function(){};
  const printVersion = mod.printVersion || function(){};
  printVersion();

  const el = (id)=>document.getElementById(id);

  // 渲染模块监控区块
  async function renderModules(){
    const list = await apiModules();
    const host = el('monitor-modules'); if(!host) return; host.innerHTML='';
    list.forEach(name=>{
      const card = document.createElement('div');
      card.className = 'card';
      card.setAttribute('data-module', name);
      card.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><div style="font-weight:700">${name}</div><div class="meta">脚本</div></div><div style="display:flex;gap:8px"><button class="btn" data-act="run" data-name="${name}" data-uid="act-run-${name}">运行</button><button class="btn" data-act="status" data-uid="act-status-${name}">状态</button><button class="btn" data-act="curl" data-name="${name}" data-uid="act-curl-${name}">调用</button></div>`;
      host.appendChild(card);
    });
    bindQuickActions(host);
  }

  // 渲染模块状态区块
  async function renderStatus(){
    const j = await apiStatus();
    const pre = el('monitor-status');
    if(pre) {
      if(typeof j === 'string') {
        pre.textContent = j;
      } else {
        pre.textContent = JSON.stringify(j, null, 2);
      }
    }
  }

  // 占位面板联动
  const phHost = document.getElementById('monitor-ph');
  document.querySelectorAll('[data-ph]').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const key = btn.getAttribute('data-ph');
      try{ const r = await fetch(`/api/placeholder/${key}`); const j = await r.json(); phHost.textContent = JSON.stringify(j, null, 2); }catch(e){ phHost.textContent = String(e); }
    });
  });

  // 日志区块联动
  let logs = ["[10:00:01] 系统启动"]; let logSSE=null;
  function renderLogsBox(){
    const logBox = document.getElementById('logBox');
    const filterEl = document.getElementById('logFilter');
    if(!logBox || !filterEl) return;
    const filter = (filterEl.value||'').trim().toLowerCase();
    let filtered = logs;
    if(filter) filtered = logs.filter(l => String(l).toLowerCase().includes(filter));
    logBox.innerText = filtered.map(l => typeof l === 'string' ? l : JSON.stringify(l)).join("\n");
  }
  function startLogSSE(){ try{ if(logSSE){ logSSE.close(); logSSE=null; } const tok = auth?.getToken?.(); const url = tok ? `/api/sse/logs?token=${encodeURIComponent(tok)}` : '/api/sse/logs'; logSSE = new EventSource(url); logSSE.onmessage=(ev)=>{ if(ev && ev.data){ try{ const payload = JSON.parse(ev.data); if(Array.isArray(payload.lines)){ logs = logs.concat(payload.lines).slice(-1000); renderLogsBox(); } } catch { logs.push(ev.data); renderLogsBox(); } } }; logSSE.onerror = ()=>{ if(logSSE){ logSSE.close(); logSSE=null; } }; }catch(e){ }
  }
  async function renderLogs(){ try{ const resp = await fetch('./data/logs.txt?t=' + Date.now()); if(resp.ok){ const text = await resp.text(); logs = text.split(/\n/).filter(Boolean); } }catch(e){ } renderLogsBox(); }

  // 已执行脚本区块联动
  let executedScripts = []; let selectedScript = null;
  async function renderExecutedScripts(){ const ul = document.getElementById('executedScripts'); if(!ul) return; ul.innerHTML=''; try{ const st = await fetch('./data/crawler_status.json?t=' + Date.now()).then(r=>r.ok?r.json():null); const list = new Set(executedScripts); if(st && st.running && st.script) list.add(st.script); Array.from(list).forEach(s=>{ const li=document.createElement('li'); li.textContent=s; ul.appendChild(li); }); }catch{ executedScripts.forEach(s=>{ const li=document.createElement('li'); li.textContent=s; ul.appendChild(li); }); } }

  // 脚本列表区块联动
  function renderScriptList(){ const ul = document.getElementById('scriptList'); const filterEl = document.getElementById('scriptFilter'); if(!ul || !filterEl) return; const filter = (filterEl.value||'').trim().toLowerCase(); Array.from(ul.children).forEach(li=>{ li.style.display = li.textContent.toLowerCase().includes(filter) ? '' : 'none'; li.onclick = ()=>{ selectedScript = li.dataset.script; logs.push(`[${new Date().toLocaleTimeString()}] 选中脚本: ${selectedScript}`); renderLogs(); }; }); }

  // 启动脚本联动
  window.startScript = async function(){ if(!selectedScript) return alert("请先选择脚本"); const time = Number(document.getElementById("pollingTime").value || 3); const path = document.getElementById("pathInput").value || '/data/tasks'; try{ const resp = await fetch('/api/crawler/start',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ script: selectedScript, interval: time, path }) }); const text = await resp.text(); logs.push(`[${new Date().toLocaleTimeString()}] 启动脚本: ${selectedScript} | 响应: ${text}`); executedScripts.push(selectedScript); }catch(e){ logs.push(`[${new Date().toLocaleTimeString()}] 启动失败: ${String(e)}`); } renderLogs(); renderExecutedScripts(); }

  // Charts
  const cpuSeriesData=[]; const memSeriesData=[]; const tsLabels=[];
  async function updateProgress(){ try{ const resp = await fetch('./data/stats.json?t=' + Date.now()); if(resp.ok){ const stats = await resp.json(); if(stats && stats.modules && Array.isArray(stats.modules)){ /* progress mapping omitted for brevity */ } if(stats && stats.series){ if(Array.isArray(stats.series.cpu)){ cpuSeriesData.length=0; tsLabels.length=0; stats.series.cpu.forEach(p=>{ cpuSeriesData.push(p); const ts=Number(p.t||0); const d=new Date(ts*1000); tsLabels.push(isFinite(d.getTime()) ? `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}` : ''); }); } if(Array.isArray(stats.series.mem)){ memSeriesData.length=0; stats.series.mem.forEach(p=>memSeriesData.push(p)); } } } }catch(e){ /* fallback omitted */ } }

  function updateChart(){ /* bind to echarts instance if present */ }

  // 主动刷新所有区块
  async function updateUI(){ await renderModules(); await renderStatus(); updateProgress(); renderLogs(); renderExecutedScripts(); renderScriptList(); updateChart(); }
  setInterval(updateUI, 3000); updateUI(); startLogSSE();

  // === Dashboard features & unified launch ===
  let dashboard = { role: 'user', features: ['collect','enum','recognize','crack','logs','config'] };
  async function fetchFeatures(){
    // 取消功能联动的可见性管理：默认全部功能可见，不再基于后端 features/role 进行隐藏
    const ids = ['feature-collect','btn-collect-launch','feature-enum','btn-enum-launch','feature-recognize','btn-recognize-launch','feature-crack','btn-crack-launch','feature-logs','feature-config','btn-config-apply','btn-export-all'];
    ids.forEach(id=>{ const el=document.getElementById(id); if(el){ el.style.display=''; } });
  }

  // 监控状态刷新与错误处理
  async function updateMonitorStatus() {
    try {
      const res = await fetch('/api/monitor/status', { headers: { ...auth.getAuthHeaders?.() } });
      if (!res.ok) throw new Error('监控接口异常');
      const data = await res.json();
      document.getElementById('monitor-status').textContent = data.status || 'OK';
      document.getElementById('monitor-status').className = 'ok';
    } catch (e) {
      document.getElementById('monitor-status').textContent = 'ERROR';
      document.getElementById('monitor-status').className = 'fail';
    }
  }

  // 日志列表刷新与错误处理
  async function updateLogs() {
    try {
      const res = await fetch('/api/monitor/logs', { headers: { ...auth.getAuthHeaders?.() } });
      if (!res.ok) throw new Error('日志接口异常');
      const data = await res.json();
      const list = document.getElementById('logs-list');
      list.innerHTML = '';
      (data.logs || []).forEach(log => {
        const li = document.createElement('li');
        li.textContent = log;
        list.appendChild(li);
      });
    } catch (e) {
      document.getElementById('logs-list').innerHTML = '<li>加载失败</li>';
    }
  }

  // 事件绑定与初始化
  window.addEventListener('DOMContentLoaded', () => {
    updateMonitorStatus();
    updateLogs();
    document.getElementById('refresh-status').onclick = updateMonitorStatus;
    document.getElementById('refresh-logs').onclick = updateLogs;
  });
  async function unifiedLaunch(feature, script, params){
    try{
      const r = await fetch('/api/dashboard/launch',{ method:'POST', headers:{'Content-Type':'application/json', ...auth.getAuthHeaders()}, body: JSON.stringify({ feature, script, params }) });
      const j = await r.json(); logs.push(`[${new Date().toLocaleTimeString()}] 大屏启动: ${feature}/${script} -> ${j.code===0?'成功':'失败'}`);
    }catch(e){ logs.push(`[${new Date().toLocaleTimeString()}] 大屏启动失败: ${String(e)}`); }
    renderLogs();
  }

  // 绑定统一启动按钮（保持 JS 控制，不直接改 HTML）
  function bindDashboardActions(){
    const q = (id)=>document.getElementById(id);
    q('btn-collect-launch')?.addEventListener('click', ()=> unifiedLaunch('collect','spider', { url: q('collectUrl')?.value || 'https://example.com' }));
    q('btn-enum-launch')?.addEventListener('click',   ()=> unifiedLaunch('enum','enum_task', { target: q('enumTarget')?.value || '' }));
    q('btn-recognize-launch')?.addEventListener('click', ()=> unifiedLaunch('recognize','recognizer', { text: q('recognizeText')?.value || '' }));
    q('btn-crack-launch')?.addEventListener('click',  ()=> unifiedLaunch('crack','cracker', { hash: q('crackHash')?.value || '' }));
    q('btn-config-apply')?.addEventListener('click',  async ()=>{ try{ const lv = Number(q('configLevel')?.value || 0); const r = await fetch('/api/policy/set',{ method:'POST', headers:{'Content-Type':'application/json', ...auth.getAuthHeaders()}, body: JSON.stringify({ level: lv }) }); const j = await r.json(); logs.push(`[${new Date().toLocaleTimeString()}] 配置默认级别 -> ${JSON.stringify(j)}`);}catch(e){ logs.push(`[${new Date().toLocaleTimeString()}] 配置失败: ${String(e)}`);} renderLogs(); });
  }

  // optional auto login demo (can be replaced by real login UI)
  // 已移除演示自动登录，统一使用登录页鉴权
  await fetchFeatures(); bindDashboardActions();

  // AI optimize suggestions (panel)
  (function(){ const input=document.getElementById('aiErrorInputMon'); const btn=document.getElementById('aiOptimizeSubmitMon'); const clr=document.getElementById('aiOptimizeClearMon'); const out=document.getElementById('aiOptimizeResultMon'); function render(obj){ try{ const data=(obj && obj.data && obj.data.data) ? obj.data.data : (obj && obj.data ? obj.data : obj); out.textContent = (data && data.status === 'success') ? JSON.stringify(data.data, null, 2) : JSON.stringify(obj, null, 2); }catch(e){ out.textContent = String(e); } } btn?.addEventListener('click', async ()=>{ const text = input.value || ''; if(!text){ out.textContent = '请先粘贴错误文本。'; return; } btn.disabled = true; out.textContent = '提交中...'; try{ const res = await (window.AI && window.AI.optimizeError ? window.AI.optimizeError(text, { page: 'monitor.html' }) : Promise.resolve({code:1,error:'AI helper missing'})); render(res);}catch(err){ out.textContent = String(err); } btn.disabled=false; }); clr?.addEventListener('click', ()=>{ input.value=''; out.textContent=''; }); })();

  // AI_OPTIMIZE cards from SSE logs
  (function(){ const listEl=document.getElementById('aiOptimizeList'); function pushCardFromObj(data){ try{ if(data && data.type==='AI_OPTIMIZE'){ const card=document.createElement('div'); card.style.border='1px solid rgba(29,240,255,0.25)'; card.style.borderRadius='6px'; card.style.padding='8px'; card.style.background='#0a0f1e'; const result=(data.result && data.result.data) ? data.result.data : data.result; const summary=result?.data?.summary || '（无摘要）'; const fixes=Array.isArray(result?.data?.fixes)? result.data.fixes : []; card.innerHTML = `
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div style="font-weight:600;color:#1de9b6;">${summary}</div>
                <div style="display:flex;gap:6px">
                  <button class="copy-btn" style="background:#1de9b6;color:#000;border:none;padding:4px 8px;border-radius:4px;cursor:pointer">复制</button>
                  <button class="apply-btn" style="background:#03a9f4;color:#000;border:none;padding:4px 8px;border-radius:4px;cursor:pointer">生成补丁</button>
                  <button class="preview-btn" style="background:#ff9800;color:#000;border:none;padding:4px 8px;border-radius:4px;cursor:pointer">预演补丁</button>
                </div>
              </div>
              <div style="margin-top:6px;color:#bfefff;font-size:12px">错误片段：${(data.error_text||'').slice(0,200)}</div>
              <div style="margin-top:6px">${(fixes||[]).slice(0,3).map((f,idx)=>{ const steps=Array.isArray(f.steps)? f.steps.slice(0,3).join('；') : ''; return `<div style='margin-top:4px'><span style='color:#1de9b6'>建议${idx+1}：</span>${(f.title||'')}${steps? '（'+steps+'）':''}</div>`; }).join('')}</div>`; card.querySelector('.copy-btn')?.addEventListener('click', ()=>{ try{ navigator.clipboard.writeText(JSON.stringify(result,null,2)); }catch(_){ } }); card.querySelector('.apply-btn')?.addEventListener('click', async ()=>{ try{ const fix = fixes && fixes[0] ? fixes[0] : { title: summary, files: [] }; const r = await fetch('/ai/optimize/apply',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ fix, context: { page: 'monitor.html' } }) }); const j = await r.json(); alert('补丁预览:\n'+JSON.stringify(j, null, 2)); }catch(err){ alert(String(err)); } }); card.querySelector('.preview-btn')?.addEventListener('click', async ()=>{ try{ const fix = fixes && fixes[0] ? fixes[0] : { title: summary, files: [] }; const patch = fix.patch || { file: (fix.files||[])[0] || '', diff: fix.diff || '' }; const r = await fetch('/ai/optimize/patch-preview',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ patch }) }); const j = await r.json(); alert('预演结果:\n'+JSON.stringify(j, null, 2)); }catch(err){ alert(String(err)); } }); if(listEl){ listEl.prepend(card); while(listEl.children.length>20){ listEl.removeChild(listEl.lastChild); } } } }catch(_){ } }
    // Hook into existing SSE stream
    const origOnMessage = (msg)=>{ try{ const payload = JSON.parse(msg); if(Array.isArray(payload.lines)) payload.lines.forEach(line=>{ if(typeof line === 'object') pushCardFromObj(line); }); }catch(_){ } };
    // replace startLogSSE to also feed AI cards
    const _startLogSSE = startLogSSE;
    startLogSSE = function(){ try{ if(logSSE){ logSSE.close(); logSSE=null; } const tok = auth?.getToken?.(); const url = tok ? `/api/sse/logs?token=${encodeURIComponent(tok)}` : '/api/sse/logs'; logSSE = new EventSource(url); logSSE.onmessage=(ev)=>{ if(ev && ev.data){ try{ const payload = JSON.parse(ev.data); if(Array.isArray(payload.lines)){ logs = logs.concat(payload.lines).slice(-1000); renderLogsBox(); payload.lines.forEach(line=>{ if(typeof line === 'object') origOnMessage(JSON.stringify(line)); }); } } catch { logs.push(ev.data); renderLogsBox(); } } }; logSSE.onerror = ()=>{ if(logSSE){ logSSE.close(); logSSE=null; } }; }catch(e){ }
    };
  })();
})();

// 页面完成初始化后显示（与 monitor.html 的 body 初始隐藏配合）
try{
  document.addEventListener('DOMContentLoaded', function(){ if(document && document.body){ document.body.style.opacity = '1'; } });
}catch(_){ }

// === Read-only circuit state display ===
(function(){
  function renderCircuit(j){
    var host = document.getElementById('circuit-state'); if(!host) return;
    try{
      var d = j && j.data ? j.data : j;
      host.textContent = JSON.stringify(d, null, 2);
    }catch(e){ host.textContent = String(e); }
  }
  async function load(){
    try{
      const r = await fetch('/api/scheduler/circuit');
      const j = await r.json();
      renderCircuit(j);
    }catch(e){ var host=document.getElementById('circuit-state'); if(host){ host.textContent=String(e); } }
  }
  document.addEventListener('DOMContentLoaded', load);
})();

// 页面完成初始化后显示（与 monitor.html 的 body 初始隐藏配合）
try{
  document.addEventListener('DOMContentLoaded', function(){
    if(document && document.body){ document.body.style.opacity = '1'; }
  });
}catch(_){ }

// === Read-only policy level display ===
(function(){
  function ensurePolicyPanel(){
    var host = document.getElementById('policy-level');
    if(!host){
      host = document.createElement('pre');
      host.id = 'policy-level';
      host.style.whiteSpace = 'pre-wrap';
      host.style.background = '#0a0f1e';
      host.style.color = '#bfefff';
      host.style.padding = '8px';
      host.style.border = '1px solid rgba(29,240,255,0.25)';
      host.style.borderRadius = '6px';
      // Try to place it near circuit-state if present
      var cs = document.getElementById('circuit-state');
      if(cs && cs.parentNode){ cs.parentNode.appendChild(host); }
      else { document.body.appendChild(host); }
    }
    return host;
  }
  function renderPolicy(j){
    var host = ensurePolicyPanel();
    try{
      var d = j && j.data ? j.data : j;
      var level = (d && (d.policy_level ?? d.level)) ?? 'unknown';
      host.textContent = '当前策略等级: ' + level + '\n' + JSON.stringify(d, null, 2);
    }catch(e){ host.textContent = String(e); }
  }
  async function load(){
    try{
      const r = await fetch('/api/policy/get');
      const j = await r.json();
      renderPolicy(j);
    }catch(e){ var host=ensurePolicyPanel(); host.textContent='策略加载失败: '+String(e); }
  }
  document.addEventListener('DOMContentLoaded', load);
})();
