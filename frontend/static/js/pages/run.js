// stripped page controller
void 0;
// Entry script for run page: render UI skeleton, load scripts list, submit runs, render results, toast errors, health indicator
// Prefer unified module mounting; fallback to local implementation when module missing
// Minimal entry: delegate to module, no business logic here
  (async ()=>{
    try {
      const { mountModule } = await import('../modules/registry.js?v=__ASSET_VERSION__');
      const ok = await mountModule('run'); if (ok) return;
    } catch (e1) {
      try {
        const { mountModule } = await import('/static/js/modules/registry.js?v=__ASSET_VERSION__');
        const ok = await mountModule('run'); if (ok) return;
      } catch (e2) {
        console.warn('Run module registry load failed', e1, e2);
      }
    }
    // Fallback: mount page module directly
    try {
      const mod = await import('../modules/run.js?v=__ASSET_VERSION__');
      if (mod?.mount) await mod.mount(document.getElementById('run-root')||document.body);
    } catch (e3) {
      try {
        const mod = await import('/static/js/modules/run.js?v=__ASSET_VERSION__');
        if (mod?.mount) await mod.mount(document.getElementById('run-root')||document.body);
      } catch (e4) {
        console.error('Run module load failed', e3, e4);
      }
    }
  })();

// Minimal clickable module placeholder guard
(function ensureMinimal(){
  const root = document.getElementById('run-root');
  if (root && !root.children.length) {
    const section = document.createElement('section');
    section.className = 'card';
    const btn = document.createElement('button');
    btn.className = 'btn';
    btn.textContent = '打开任务中心';
    btn.onclick = ()=> alert('任务中心占位（后续由模块渲染）');
    section.appendChild(btn);
    root.appendChild(section);
  }
})();

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!res.ok) throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
  return data;
}

function showToastSafe(msg, type = 'info') {
  if (window.showToast) {
    window.showToast({ message: msg, type });
  } else {
    console[type === 'error' ? 'error' : 'log']('[toast]', msg);
  }
}

function $(id) { return document.getElementById(id); }

function html(strings, ...vals) {
  const s = strings.reduce((acc, cur, i) => acc + cur + (i < vals.length ? vals[i] : ''), '');
  const tpl = document.createElement('template');
  tpl.innerHTML = s.trim();
  return tpl.content;
}

// Render Topbar and base panels
function renderSkeleton() {
  // 顶部导航交由 common/topbar.js 统一渲染，这里不再覆盖 header#topbar 内容
  const topbar = $('topbar'); if (topbar) { /* ensure exists only */ }

  const left = $('left-pane');
  if (left) {
    left.innerHTML = '';
    left.appendChild(html`
      <section class="card" id="panel-hosts">
        <h3>总体 / Hosts</h3>
        <div class="kpi" id="hostKPI">—</div>
        <div class="module-grid" id="hostList"></div>
      </section>
      <section class="card" id="panel-controls">
        <h3>控制面板</h3>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn" id="startBtn">Start</button>
          <button class="btn" id="stopBtn">Stop</button>
          <button class="btn" id="refreshBtn">刷新</button>
        </div>
        <div style="margin-top:8px;display:grid;grid-template-columns:1fr;gap:8px">
          <label>选择脚本<select id="scriptSelect"></select></label>
          <label>参数(JSON)<textarea id="paramsInput" rows="6" placeholder='{"key":"value"}'></textarea></label>
          <button class="btn" id="runBtn">运行脚本</button>
        </div>
      </section>
      <section class="card" id="panel-task-center">
        <h3>任务中心</h3>
        <div class="module-grid" id="taskCenterGrid"></div>
      </section>
    `);
  }

  const center = $('center-panels');
  if (center) {
    center.innerHTML = '';
    center.appendChild(html`
      <div class="card">
        <h3>CPU / Memory</h3>
        <div id="cpuChart" class="chart-placeholder"></div>
      </div>
      <div class="card">
        <h3>模块占比 & AI 指标</h3>
        <div id="moduleChart" class="chart-placeholder"></div>
        <div style="display:flex;gap:8px;margin-top:8px">
          <div class="kpi" id="aiModel">AI Model</div>
          <div class="kpi" id="tokenRate">Token/s</div>
          <div class="kpi" id="accuracy">Accuracy</div>
        </div>
      </div>
      <div class="card" id="aiPipelineCard">
        <h3>自然语言联动入口</h3>
        <div class="card-note">通过 /api/ai/pipeline 触发联动</div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <input id="ai-prompt-input" placeholder="输入任务（中文）" style="flex:1;min-width:280px" />
          <button id="ai-run-btn" class="btn">运行 AI</button>
        </div>
        <pre id="ai-result" style="margin-top:8px;white-space:pre-wrap;max-height:240px;overflow:auto"></pre>
      </div>
      <div class="card">
        <h3>项目任务与部署状态</h3>
        <div class="card-note">来自 PROJECT_STATUS.md</div>
        <div id="project-status"></div>
      </div>
      <div class="card">
        <h3>运行结果</h3>
        <pre id="runResult" class="chart-placeholder" style="height:auto"></pre>
      </div>
    `);
  }

  const right = $('right-panels');
  if (right) {
    right.innerHTML = '';
    right.appendChild(html`
      <div class="card" id="aiOptimizeCard">
        <h3>AI 优化建议</h3>
        <textarea id="aiErrorInput" placeholder="粘贴终端错误或日志片段" style="width:100%;height:120px"></textarea>
        <div style="display:flex;gap:8px;margin-top:8px">
          <button class="btn" id="aiOptimizeSubmit">提交到 AI</button>
          <button class="btn" id="aiOptimizeClear">清空</button>
        </div>
        <pre id="aiOptimizeResult" style="margin-top:8px;max-height:240px;overflow:auto;white-space:pre-wrap"></pre>
        <div id="aiOptimizeFeed" style="margin-top:8px">
          <div style="font-weight:700;margin-bottom:6px">实时建议流</div>
          <div id="aiOptimizeList" style="display:flex;flex-direction:column;gap:8px"></div>
        </div>
      </div>
      <div class="card advanced-mini">
        <h3>高级功能</h3>
        <div class="advanced-mini-grid">
          <span class="advanced-mini-item">AI高级联动</span>
          <span class="advanced-mini-item">交叉解析</span>
          <span class="advanced-mini-item">反追反穿</span>
          <span class="advanced-mini-item">极限突破</span>
          <span class="advanced-mini-item">破译挑战</span>
        </div>
      </div>
    `);
  }
}

async function loadScripts() {
  const select = $('scriptSelect');
  if (!select) return;
  try {
    const list = await fetchJSON('/api/scripts');
    const items = Array.isArray(list) ? list : (list.scripts || []);
    select.innerHTML = '';
    for (const name of items) {
      const opt = document.createElement('option');
      opt.value = name; opt.textContent = name;
      select.appendChild(opt);
    }
  } catch (e) {
    showToastSafe(`加载脚本列表失败: ${e.message}`, 'error');
  }
}

function parseParams(text) {
  if (!text || !text.trim()) return {};
  try { return JSON.parse(text); } catch (e) {
    throw new Error('参数不是合法 JSON');
  }
}

async function submitRun() {
  const select = $('scriptSelect');
  const paramsEl = $('paramsInput');
  const resultEl = $('runResult');
  const btn = $('runBtn');
  if (!select || !paramsEl || !resultEl) return;
  const name = select.value;
  let params;
  try { params = parseParams(paramsEl.value); } catch (e) { showToastSafe(e.message, 'error'); return; }
  try {
    if (btn) { btn.disabled = true; btn.textContent = '运行中...'; }
    const res = await fetchJSON('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, params })
    });
    resultEl.textContent = typeof res === 'string' ? res : JSON.stringify(res, null, 2);
    showToastSafe('脚本运行完成', 'success');
  } catch (e) {
    showToastSafe(`运行失败: ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '运行脚本'; }
  }
}

// AI pipeline & optimize integrations
async function submitAI() {
  const input = $('ai-prompt-input');
  const out = $('ai-result');
  const btn = $('ai-run-btn');
  if (!input || !out) return;
  const prompt = input.value.trim();
  if (!prompt) { showToastSafe('请输入任务', 'error'); return; }
  try {
    if (btn) { btn.disabled = true; btn.textContent = '运行中...'; }
    const res = await fetchJSON('/api/ai/pipeline', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ prompt })
    });
    out.textContent = typeof res === 'string' ? res : JSON.stringify(res, null, 2);
  } catch (e) {
    showToastSafe(`AI 联动失败: ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '运行 AI'; }
  }
}

async function submitOptimize() {
  const input = $('aiErrorInput');
  const out = $('aiOptimizeResult');
  const feed = $('aiOptimizeList');
  const btn = $('aiOptimizeSubmit');
  if (!input || !out || !feed) return;
  const text = input.value.trim();
  if (!text) { showToastSafe('请粘贴错误或日志', 'error'); return; }
  try {
    if (btn) { btn.disabled = true; btn.textContent = '提交中...'; }
    const res = await fetchJSON('/api/ai/optimize', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ text })
    });
    const pretty = typeof res === 'string' ? res : JSON.stringify(res, null, 2);
    out.textContent = pretty;
    const item = document.createElement('div');
    item.className = 'feed-item';
    item.textContent = pretty.slice(0, 240);
    feed.prepend(item);
  } catch (e) {
    showToastSafe(`AI 优化失败: ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '提交到 AI'; }
  }
}

function bindEvents() {
  const btn = $('runBtn');
  if (btn) btn.addEventListener('click', submitRun);

  const fullBtn = $('fullBtn');
  if (fullBtn) fullBtn.addEventListener('click', () => {
    const el = document.documentElement;
    if (!document.fullscreenElement) el.requestFullscreen().catch(()=>{});
    else document.exitFullscreen().catch(()=>{});
  });

  const aiBtn = $('ai-run-btn');
  if (aiBtn) aiBtn.addEventListener('click', submitAI);

  const optBtn = $('aiOptimizeSubmit');
  const clrBtn = $('aiOptimizeClear');
  if (optBtn) optBtn.addEventListener('click', submitOptimize);
  if (clrBtn) clrBtn.addEventListener('click', () => {
    const input = $('aiErrorInput'); const out = $('aiOptimizeResult');
    if (input) input.value = ''; if (out) out.textContent = '';
  });
}

// Health indicator polling
async function pollHealth() {
  const dot = $('ghi-dot');
  const text = $('ghi-text');
  if (!dot || !text) return;
  try {
    const res = await fetch('/health');
    const ok = res.ok;
    dot.style.background = ok ? '#22c55e' : '#9ca3af';
    text.textContent = ok ? '健康' : '异常';
  } catch {
    dot.style.background = '#9ca3af';
    text.textContent = '离线';
  }
}

function startHealthLoop() {
  pollHealth();
  setInterval(pollHealth, 5000);
}

// Charts: switch to local charting module
async function renderCharts() {
  try {
    const { ensureChartLib, renderCpuLine, renderModuleDonut } = await import('/static/js/components/charting.js');
    await ensureChartLib();
    const cpuEl = $('cpuChart');
    const modEl = $('moduleChart');
    if (cpuEl) await renderCpuLine(cpuEl);
    if (modEl) await renderModuleDonut(modEl);
  } catch (e) {
    showToastSafe(`图表渲染失败: ${e.message}`, 'error');
  }
}

// Initialization handled by modules/run.js
(function(){
  // 取消登录限制：不再强制跳转登录页（保留后续请求带头）
  (async function(){ try{ const mod=await import('/static/js/auth.js'); mod.auth.getToken?.(); }catch{} })();
  // ECharts loader (local first, CDN fallback)
  function loadScript(src){return new Promise((res,rej)=>{const s=document.createElement('script');s.src=src;s.async=true;s.onload=()=>res(src);s.onerror=()=>rej(new Error('fail:'+src));document.head.appendChild(s);});}
  const local = '/static/libs/echarts/echarts.min.js';
  const cdn = 'https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js';
  loadScript(local).catch(()=>loadScript(cdn));

  // Diff preview helper
  function renderDiffPreview(container, diffText){
    const lines=(diffText||'').split('\n'); container.innerHTML=''; let lineNo=1; const frag=document.createDocumentFragment();
    let neutralBuf=[]; function addLine(text,bg){const row=document.createElement('div'); const no=document.createElement('span'); const body=document.createElement('span'); no.textContent=String(lineNo++).padStart(4,' '); no.style.display='inline-block'; no.style.width='3em'; no.style.color='#94a3b8'; body.textContent=text.replace(/^\+|^-/, ''); row.style.background=bg; row.style.fontFamily='monospace'; row.style.whiteSpace='pre'; row.appendChild(no); row.appendChild(body); frag.appendChild(row);} 
    function flushNeutral(){ if(neutralBuf.length>8){ const toggler=document.createElement('button'); toggler.textContent=`展开上下文（${neutralBuf.length} 行）`; toggler.className='btn'; toggler.style.margin='4px 0'; const block=document.createElement('div'); block.style.display='none'; neutralBuf.forEach(t=> addLine(t,'#f6f8fa')); toggler.onclick=()=>{ block.style.display = block.style.display==='none'?'block':'none'; }; container.appendChild(toggler); container.appendChild(block);} else { neutralBuf.forEach(t=> addLine(t,'#f6f8fa')); } neutralBuf=[]; }
    lines.forEach(l=>{ if(l.startsWith('+')){ flushNeutral(); addLine(l,'#e6ffed'); } else if(l.startsWith('-')){ flushNeutral(); addLine(l,'#ffeef0'); } else { neutralBuf.push(l); } });
    flushNeutral(); container.appendChild(frag);
  }
  window.renderDiffPreview = renderDiffPreview;

  // Topbar controls
  const toggleThemeBtn = document.getElementById('toggleTheme');
  const fullBtn = document.getElementById('fullBtn');
  toggleThemeBtn && (toggleThemeBtn.onclick=()=>{document.body.setAttribute('data-theme',document.body.getAttribute('data-theme')==='dark'?'light':'dark');});
  fullBtn && (fullBtn.onclick=()=>{document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();});

  // 任务中心约束：禁止跳转其他页面（屏蔽常见导航行为）
  // 移除强拦截跨页跳转，避免覆盖只读属性导致错误；允许正常导航

  // 权限来源识别：login.html vs index.html
  (function sourcePerms(){
    try{
      const fromLogin = sessionStorage.getItem('from_login') === '1';
      const fromIndexSuper = sessionStorage.getItem('index_superadmin') === '1' && (localStorage.getItem('yl_user_role')==='superadmin');
      // 仅显示来源提示，不做任何元素隐藏/显示控制
      const tip=document.createElement('div'); tip.style.position='fixed'; tip.style.left='16px'; tip.style.bottom='24px'; tip.style.zIndex='9999'; tip.style.padding='6px 10px'; tip.style.borderRadius='8px'; tip.style.background='#0a0f1e'; tip.style.color='#93c5fd'; tip.style.border='1px solid rgba(29,240,255,0.35)'; tip.textContent = fromIndexSuper? '入口：index（超级管理员）' : '入口：login'; document.body.appendChild(tip);
    }catch(_){ }
  })();

  // Charts
  function initCharts(){
    if(!window.echarts) { setTimeout(initCharts, 200); return; }
    const cpuChart = echarts.init(document.getElementById('cpuChart'));
    cpuChart.setOption({ backgroundColor:'transparent', tooltip:{trigger:'axis'}, xAxis:{ type:'category', boundaryGap:false, data:['0','1','2','3','4','5','6','7','8','9','10'], axisLine:{lineStyle:{color:'#1df0ff'}} }, yAxis:{ type:'value', axisLine:{lineStyle:{color:'#1df0ff'}}, splitLine:{lineStyle:{color:'rgba(29,240,255,0.1)'}} }, series:[ { name:'CPU', type:'line', data:[20,30,25,40,35,50,45,60,55,65,70], smooth:true, lineStyle:{color:'#1df0ff',width:2}, areaStyle:{color:'rgba(29,240,255,0.2)'} }, { name:'Memory', type:'line', data:[30,40,35,50,45,60,55,70,65,75,80], smooth:true, lineStyle:{color:'#00ff9d',width:2}, areaStyle:{color:'rgba(0,255,157,0.2)'} } ] });
    const moduleChart = echarts.init(document.getElementById('moduleChart'));
    moduleChart.setOption({ backgroundColor:'transparent', tooltip:{trigger:'axis'}, xAxis:{ type:'category', data:['模块A','模块B','模块C','模块D'], axisLine:{lineStyle:{color:'#1df0ff'}} }, yAxis:{ type:'value', axisLine:{lineStyle:{color:'#1df0ff'}}, splitLine:{lineStyle:{color:'rgba(29,240,255,0.1)'}} }, series:[ { name:'占比', type:'bar', data:[40,60,30,70], itemStyle:{color:'#1df0ff',borderRadius:4}, barWidth:'40%' } ] });
    setInterval(()=>{
      const m=document.getElementById('aiModel'); const t=document.getElementById('tokenRate'); const a=document.getElementById('accuracy');
      if(m) m.innerText='AI-'+(Math.floor(Math.random()*5)+1); if(t) t.innerText=(Math.floor(Math.random()*200)+50)+' Token/s'; if(a) a.innerText=(Math.floor(Math.random()*50)+50)+' %';
    },2000);
  }
  initCharts();

  // Animated background
  (function(){
    const canvas = document.getElementById('bgCanvas'); if(!canvas) return; const ctx = canvas.getContext('2d');
    function resize(){ canvas.width=window.innerWidth; canvas.height=window.innerHeight; }
    resize();
    let nodes = []; for(let i=0;i<80;i++){ nodes.push({ x:Math.random()*canvas.width, y:Math.random()*canvas.height, vx:(Math.random()-0.5)*0.5, vy:(Math.random()-0.5)*0.5, size:Math.random()*2+1 }); }
    function animate(){ ctx.clearRect(0,0,canvas.width,canvas.height); for(let i=0;i<nodes.length;i++){ const n=nodes[i]; n.x+=n.vx; n.y+=n.vy; if(n.x>canvas.width||n.x<0)n.vx*=-1; if(n.y>canvas.height||n.y<0)n.vy*=-1; ctx.fillStyle='rgba(29,240,255,0.5)'; ctx.beginPath(); ctx.arc(n.x,n.y,n.size,0,2*Math.PI); ctx.fill(); for(let j=i+1;j<nodes.length;j++){ const nx=nodes[j]; const dist=Math.hypot(n.x-nx.x,n.y-nx.y); if(dist<100){ ctx.strokeStyle='rgba(29,240,255,'+(0.3-dist/300)+')'; ctx.beginPath(); ctx.moveTo(n.x,n.y); ctx.lineTo(nx.x,nx.y); ctx.stroke(); } } } requestAnimationFrame(animate); }
    animate(); window.onresize=resize;
  })();

  // 注入右上角登录状态徽标（纯 JS，不改 HTML）
  (async function(){ try{ const mod=await import('/static/js/auth.js'); const role=localStorage.getItem('yl_user_role')||'user'; const wrap=document.createElement('div'); wrap.style.position='fixed'; wrap.style.top='14px'; wrap.style.right='14px'; wrap.style.zIndex='9999'; wrap.style.display='flex'; wrap.style.gap='8px'; const badge=document.createElement('div'); badge.style.padding='6px 10px'; badge.style.borderRadius='999px'; badge.style.fontSize='12px'; badge.style.background='#0a0f1e'; badge.style.color='#1de9b6'; badge.style.border='1px solid rgba(29,240,255,0.35)'; const acc=(mod.auth.getUser?.() && mod.auth.getUser().account)||''; badge.textContent=`已登录：${acc||'用户'}｜角色：${role}`; const exit=document.createElement('button'); exit.textContent='退出登录'; exit.className='btn'; exit.style.padding='6px 10px'; exit.style.borderRadius='999px'; exit.style.background='#ef4444'; exit.style.color='#fff'; exit.style.border='none'; exit.style.cursor='pointer'; exit.onclick=()=>{ try{ (mod.auth.clearToken?.()||mod.auth.setToken?.('')); }catch(_){ } try{ localStorage.removeItem('yl_user_role'); }catch(_){ } window.location.href='/pages/login.html'; }; wrap.appendChild(badge); wrap.appendChild(exit); document.body.appendChild(wrap);}catch(_){ } })();

  // Modules grid wiring
  import('/static/js/modules.js').then(async ({ apiModules, bindQuickActions, printVersion })=>{
    // 统一鉴权头
    let authH = {}; try{ const mod = await import('/static/js/auth.js'); authH = mod.auth.getAuthHeaders?.() || {}; }catch(_){ }
    async function loadModules(){ try{ const list=await apiModules(); const grid=document.getElementById('taskCenterGrid'); const apiGrid=document.getElementById('apiModuleGrid'); if(grid){ grid.innerHTML=''; list.forEach(name=>{ const item=document.createElement('div'); item.className='module-item'; item.innerHTML=`<span>${name}</span><span style="display:flex;gap:6px"><button class="btn" data-act="run" data-name="${name}">运行</button><button class="btn" data-act="status">状态</button></span>`; grid.appendChild(item); }); bindQuickActions(grid);} if(apiGrid){ apiGrid.innerHTML=''; list.forEach(name=>{ const item=document.createElement('div'); item.className='module-item'; item.innerHTML=`<span>/api/${name}</span><span style="display:flex;gap:6px"><button class="btn" data-act="curl" data-name="${name}">调用</button></span>`; apiGrid.appendChild(item); }); bindQuickActions(apiGrid);} }catch(e){} }
    loadModules(); printVersion && printVersion(); window.addEventListener('modules:invoke',(e)=>{ console.debug('[run] invoke',e.detail); },{passive:true});
  });

  // Health check
  const healthScript=document.createElement('script'); healthScript.src='/static/js/healthcheck.js'; document.body.appendChild(healthScript);

  // AI optimize panel interactions + WS logs subscription
  (function(){
    const input=document.getElementById('aiErrorInput'); const btn=document.getElementById('aiOptimizeSubmit'); const clr=document.getElementById('aiOptimizeClear'); const out=document.getElementById('aiOptimizeResult');
    function render(obj){ try{ const data=(obj&&obj.data&&obj.data.data)?obj.data.data:(obj&&obj.data?obj.data:obj); out.textContent = data && data.status==='success' ? JSON.stringify(data.data, null, 2) : JSON.stringify(obj, null, 2); }catch(e){ out.textContent=String(e); } }
    btn?.addEventListener('click', async ()=>{ const text=input.value||''; if(!text){ out.textContent='请先粘贴错误文本。'; return;} btn.disabled=true; out.textContent='提交中...'; try{ const res= await (window.AI && window.AI.optimizeError ? window.AI.optimizeError(text,{page:'run.html'}) : Promise.resolve({code:1,error:'AI helper missing'})); render(res);}catch(err){ out.textContent=String(err);} btn.disabled=false; });
    clr?.addEventListener('click', ()=>{ input.value=''; out.textContent=''; });
    const listEl=document.getElementById('aiOptimizeList');
    function pushCard(payload){ try{ const data=JSON.parse(payload); if(data && data.type==='AI_OPTIMIZE'){ const card=document.createElement('div'); card.style.border='1px solid rgba(29,240,255,0.25)'; card.style.borderRadius='6px'; card.style.padding='8px'; card.style.background='#0a0f1e'; const result=(data.result && data.result.data) ? data.result.data : data.result; const summary=result?.data?.summary || '（无摘要）'; const fixes=Array.isArray(result?.data?.fixes)? result.data.fixes : []; card.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div style="font-weight:600;color:#1de9b6;">${summary}</div>
            <div style="display:flex;gap:6px">
              <button class="copy-btn" style="background:#1de9b6;color:#000;border:none;padding:4px 8px;border-radius:4px;cursor:pointer">复制</button>
              <button class="apply-btn" disabled title="先校验/测试通过再启用" style="opacity:0.6;background:#03a9f4;color:#000;border:none;padding:4px 8px;border-radius:4px;cursor:not-allowed">应用补丁</button>
              <button class="preview-btn" style="background:#ff9800;color:#000;border:none;padding:4px 8px;border-radius:4px;cursor:pointer">预演补丁</button>
              <button class="validate-btn" style="background:#8bc34a;color:#000;border:none;padding:4px 8px;border-radius:4px;cursor:pointer">校验/测试</button>
            </div>
          </div>
          <div style="margin-top:6px;color:#bfefff;font-size:12px">错误片段：${(data.error_text||'').slice(0,200)}</div>
          <div style="margin-top:6px">${(fixes||[]).slice(0,3).map((f,idx)=>{ const steps=Array.isArray(f.steps)? f.steps.slice(0,3).join('；') : ''; return `<div style='margin-top:4px'><span style='color:#1de9b6'>建议${idx+1}：</span>${(f.title||'')}${steps? '（'+steps+'）':''}</div>`; }).join('')}</div>
          <div class="diff-preview" style="margin-top:8px;border:1px dashed rgba(29,240,255,0.25);border-radius:6px;padding:6px"></div>`;
        const diffEl=card.querySelector('.diff-preview');
        card.querySelector('.copy-btn')?.addEventListener('click', ()=>{ try{ navigator.clipboard.writeText(JSON.stringify(result,null,2)); }catch(_){ } });
        const validateBtn=card.querySelector('.validate-btn'); const applyBtn=card.querySelector('.apply-btn');
        validateBtn?.addEventListener('click', async ()=>{
          try{ const fix=fixes && fixes[0] ? fixes[0] : { title: summary, files: [] }; const patch= fix.patch || { file:(fix.files||[])[0] || '', diff: fix.diff || '' };
            if(patch.diff && diffEl){ renderDiffPreview(diffEl, patch.diff);} const j1 = await fetch('/ai/optimize/patch-merge',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ patch }) }).then(r=>r.json()); if(j1.code!==0){ return alert('合并失败:\n'+JSON.stringify(j1,null,2)); } const content= j1.data && j1.data.content ? j1.data.content : '';
            const v = await fetch('/ai/optimize/patch-validate',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ files: [patch.file] }) }).then(r=>r.json()); if(v.code!==0 || !v.data.ok){ return alert('校验未通过'); }
            const t = await fetch('/ai/optimize/patch-test',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ quick: true }) }).then(r=>r.json()); if(t.code!==0 || !t.data.ok){ return alert('测试失败'); }
            applyBtn.disabled=false; applyBtn.style.opacity='1'; applyBtn.style.cursor='pointer'; applyBtn.title='';
            applyBtn.onclick = async ()=>{ if(!confirm('确认应用补丁到 '+patch.file+' ?')) return; const j2 = await fetch('/ai/optimize/patch-apply',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ patch: { file: patch.file, content }, confirm: true }) }).then(r=>r.json()); if(j2.code===0){ alert('应用成功: '+j2.data.file+'\n正在刷新健康状态...'); try{ const h= await fetch('/health').then(r=>r.json()); alert('健康: '+JSON.stringify(h.data.ai_probe || h, null, 2)); }catch(_){ } } else { alert('应用失败:\n'+JSON.stringify(j2,null,2)); } };
          }catch(err){ alert(String(err)); }
        });
        card.querySelector('.preview-btn')?.addEventListener('click', async ()=>{ try{ const fix=fixes && fixes[0] ? fixes[0] : { title: summary, files: [] }; const patch= fix.patch || { file:(fix.files||[])[0] || '', diff: fix.diff || '' }; const j = await fetch('/ai/optimize/patch-preview',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ patch }) }).then(r=>r.json()); alert('预演结果:\n'+JSON.stringify(j,null,2)); if(patch.diff && diffEl){ renderDiffPreview(diffEl, patch.diff);} }catch(err){ alert(String(err)); } });
        if(listEl){ listEl.prepend(card); while(listEl.children.length>20){ listEl.removeChild(listEl.lastChild); } }
      } }catch(_){} }
    try{ const ws=new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws/logs'); ws.onmessage=(ev)=>{ pushCard(ev.data); }; }catch(_){}
  })();

  // Minimal floating button for optimize
  (function(){ const btn=document.createElement('button'); btn.textContent='AI 优化错误'; btn.className='btn'; btn.style.position='fixed'; btn.style.right='16px'; btn.style.bottom='64px'; btn.style.zIndex='99'; document.body.appendChild(btn); btn.addEventListener('click', async ()=>{ const text=prompt('粘贴终端错误或日志片段'); if(!text) return; btn.disabled=true; const res = await (window.AI && window.AI.optimizeError ? window.AI.optimizeError(text,{page:'run.html'}) : Promise.resolve({code:1,error:'AI helper missing'})); btn.disabled=false; alert('AI返回:\n'+JSON.stringify(res,null,2)); }); })();
})();

// ==== Minimal task trigger from URL params (no polling, no monitor) ====
(function(){
  try {
    const params = new URLSearchParams(location.search);
    const nodesJson = params.get('nodes');
    const script = params.get('script');
    const param = params.get('param');
    const outEl = document.getElementById('run-result') || document.getElementById('ai-result');
    const render = (obj)=>{ try{ outEl && (outEl.textContent = JSON.stringify(obj, null, 2)); }catch(_){} };
    async function trigger(){
      let authH={}; try{ const mod=await import('/static/js/auth.js'); authH = mod.auth.getAuthHeaders?.() || {}; }catch(_){ }
      if(nodesJson){
        let nodes; try{ nodes = JSON.parse(nodesJson); }catch(_){ return; }
        const payload = { nodes: nodes, max_concurrency: 4 };
        const r = await fetch('/api/pipeline/run', { method:'POST', headers:{'Content-Type':'application/json', ...authH}, body: JSON.stringify(payload) });
        const j = await r.json(); render(j);
      } else if(script){
        let p = {}; if(param){ try{ p = JSON.parse(param); }catch(_){ p = { value: param }; } }
        const r = await fetch('/api/run', { method:'POST', headers:{'Content-Type':'application/json', ...authH}, body: JSON.stringify({ script, params: p }) });
        const j = await r.json(); render(j);
      }
    }
    // auto-trigger once when arriving from index
    trigger();
  } catch(_){}
})();
