// stripped page controller
void 0;
// API Playground: modular render + backend linkage
// Prefer unified module mounting; fallback to local implementation when module missing
(async ()=>{ try { const { mountModule } = await import('../modules/registry.js?v=__ASSET_VERSION__'); const ok = await mountModule('api-doc'); if (ok) return; } catch (_) { /* fallback to local below */ } })();
// Minimal clickable module placeholder guard
(function ensureMinimal(){
  const root = document.getElementById('api-doc-root');
  if (root && !root.children.length) {
    const section = document.createElement('section');
    section.className = 'card';
    const btn = document.createElement('button');
    btn.className = 'menu-item';
    btn.textContent = '打开 API 模块';
    btn.onclick = ()=> alert('API 模块占位（后续由模块渲染）');
    section.appendChild(btn);
    root.appendChild(section);
  }
})();
// Renders topbar, sections (bubbles, progress, mapping, quick-play), and binds actions

function $(id){ return document.getElementById(id); }

function html(strings, ...vals){
  const s = strings.reduce((a,c,i)=> a + c + (i<vals.length?vals[i]:''), '');
  const t = document.createElement('template'); t.innerHTML = s.trim();
  return t.content;
}

function showToastSafe(msg, type='info'){
  if(window.showToast){ window.showToast({ message: msg, type }); }
  else { console[type==='error'?'error':'log']('[toast]', msg); }
}

async function fetchJSON(url, opts={}){
  const res = await fetch(url, opts);
  const text = await res.text();
  let data; try{ data = JSON.parse(text); }catch{ data = text; }
  if(!res.ok) throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
  return data;
}

function renderTopbar(){
  // Unified topbar is rendered by /static/js/common/topbar.js
  const top = $('topbar'); if(!top) return;
  top.innerHTML = '';
}

async function pollHealth(){
  const dot = $('ghi-dot'); const text = $('ghi-text'); if(!dot || !text) return;
  try{ const res = await fetch('/health'); const ok = res.ok; dot.style.background = ok ? '#22c55e' : '#9ca3af'; text.textContent = ok ? '健康' : '异常'; }
  catch{ dot.style.background = '#9ca3af'; text.textContent = '离线'; }
}

function startHealthLoop(){ pollHealth(); setInterval(pollHealth, 5000); }

function renderSections(){
  const root = $('api-doc-root'); if(!root) return; root.innerHTML = '';
  if (!root) return;
  root.appendChild(html`
    <div class="card">
      <h3>冒泡检查</h3>
      <div id="ap-bubbles"></div>
    </div>
    <div class="card">
      <h3>部署进度</h3>
      <div id="api-progress" class="progress-bar-container"></div>
    </div>
    <div class="card">
      <h3>API 框架映射</h3>
      <div id="ap-framework-grid" class="grid"></div>
    </div>
    <div class="card">
      <h3>模块列表</h3>
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
        <input id="ap-fw-filter" class="menu-item" style="flex:1; border:1px solid #334155; background:#0b1220;color:#e2e8f0" placeholder="关键字筛选（模块名/端点/描述）" />
        <select id="ap-fw-sort" class="menu-item" style="border:1px solid #334155; background:#0b1220;color:#e2e8f0">
          <option value="none">默认排序</option>
          <option value="progress-desc">按进度（高→低）</option>
          <option value="progress-asc">按进度（低→高）</option>
          <option value="done">已完成优先</option>
        </select>
      </div>
      <div id="ap-modules-list" class="grid"></div>
    </div>
    <div class="card">
      <h3>快速演练</h3>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px">
        <button id="btn-health" class="menu-item">GET /health</button>
        <button id="btn-scripts" class="menu-item">GET /scripts</button>
        <button id="btn-health-retry" class="menu-item">重试 /health</button>
        <button id="btn-scripts-retry" class="menu-item">重试 /scripts</button>
        <button id="btn-all" class="menu-item">全部探测</button>
        <button id="btn-rbac" class="menu-item">GET /api/security/rbac</button>
        <button id="btn-circuit" class="menu-item">GET /api/scheduler/circuit</button>
      </div>
      <pre id="out-health" style="min-height:80px"></pre>
      <pre id="out-scripts" style="min-height:80px"></pre>
      <pre id="out-rbac" style="min-height:80px"></pre>
      <pre id="out-circuit" style="min-height:80px"></pre>
    </div>
    <div class="card">
      <h3>占位接口</h3>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px">
        <button class="menu-item" data-ph="risk">/api/placeholder/risk</button>
        <button class="menu-item" data-ph="nodes">/api/placeholder/nodes</button>
        <button class="menu-item" data-ph="ai">/api/placeholder/ai</button>
        <button class="menu-item" data-ph="identity">/api/placeholder/identity</button>
        <button class="menu-item" data-ph="reports">/api/placeholder/reports</button>
        <button class="menu-item" data-ph="automation">/api/placeholder/automation</button>
      </div>
      <div id="ap-ph-out" style="min-height:120px"></div>
    </div>
    <div class="card">
      <h3>审计报告（hx-report）</h3>
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px">
        <button id="ap-load-hx" class="menu-item">读取 logs/hx-report.json</button>
        <button id="ap-refresh-hx" class="menu-item">刷新并重载</button>
      </div>
      <div id="ap-hx-summary" class="kpi"></div>
      <div id="ap-hx-bubbles" class="grid"></div>
      <div id="ap-hx-progress" class="progress-bar-container"></div>
    </div>
  `);
  // 集成统一接口映射表视图（源：docs/统一接口映射表.md）
  try{
    const sec = document.createElement('div');
    sec.className = 'card';
    sec.innerHTML = '<h3>统一接口映射表（源）</h3><div class="small">读取 docs/统一接口映射表.md（唯一真源）</div><pre id="api-map-source" style="min-height:140px"></pre>';
    root.appendChild(sec);
    fetch('/docs/统一接口映射表.md').then(r=>r.text()).then(t=>{ const el=document.getElementById('api-map-source'); if(el) el.textContent=t; }).catch(e=>{ const el=document.getElementById('api-map-source'); if(el) el.textContent=String(e); });
  }catch(_){ }

  // 渲染 API_FULL.md 的关键示例（含代码块）
  try{
    const sec2 = document.createElement('div');
    sec2.className = 'card';
    sec2.innerHTML = '<h3>API 关键示例</h3><div class="small">来自 docs/API_FULL.md（含 JSON/Bash 代码块）</div><div id="api-full-toc" class="small" style="margin:6px 0"></div><div id="api-full-view" style="min-height:140px"></div>';
    root.appendChild(sec2);
    fetch('/docs/API_FULL.md').then(r=>r.text()).then(md=>{
      const el = document.getElementById('api-full-view'); if(!el) return;
      const escape = (s)=> s.replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
      const withCode = md
        .replace(/```json([\s\S]*?)```/g, (_,body)=>`<div class="codewrap"><button class="copybtn" data-code="${encodeURIComponent(body.trim())}">复制</button><pre><code class="lang-json">${escape(body.trim())}</code></pre></div>`)
        .replace(/```bash([\s\S]*?)```/g, (_,body)=>`<div class="codewrap"><button class="copybtn" data-code="${encodeURIComponent(body.trim())}">复制</button><pre><code class="lang-bash">${escape(body.trim())}</code></pre></div>`);
      const html = withCode
        .replace(/^### (.*$)/gim, '<h3 id="$1">$1</h3>')
        .replace(/^## (.*$)/gim, '<h2 id="$1">$1</h2>')
        .replace(/^# (.*$)/gim, '<h1 id="$1">$1</h1>')
        .replace(/^\- (.*$)/gim, '<li>$1</li>')
        .replace(/\n\n/g, '<br/><br/>' );
      el.innerHTML = html;
      // 辅助：创建请求配置弹窗
      function ensureModal(){
        let m = document.getElementById('req-modal'); if(m) return m;
        m = document.createElement('div'); m.id='req-modal'; m.style.position='fixed'; m.style.left='0'; m.style.top='0'; m.style.right='0'; m.style.bottom='0'; m.style.background='rgba(0,0,0,0.55)'; m.style.display='none'; m.style.alignItems='center'; m.style.justifyContent='center'; m.style.zIndex='9999';
        m.innerHTML = '<div style="width:620px;max-width:92vw;background:#0b1220;border:1px solid #334155;border-radius:12px;padding:12px;color:#e2e8f0"><h3 style="margin:0 0 8px">请求配置</h3><div style="display:flex;gap:8px"><textarea id="req-headers" placeholder="headers(JSON)" style="flex:1;height:120px;background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:8px;padding:8px">{}</textarea><textarea id="req-body" placeholder="body(JSON)" style="flex:1;height:120px;background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:8px;padding:8px">{}</textarea></div><div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px"><button id="req-cancel" class="menu-item">取消</button><button id="req-send" class="menu-item" style="background:#2563eb;color:#fff">发送</button></div></div>';
        document.body.appendChild(m);
        m.addEventListener('click', (e)=>{ if(e.target===m){ m.style.display='none'; } });
        m.querySelector('#req-cancel').addEventListener('click', ()=>{ m.style.display='none'; });
        return m;
      }
      const reqContext = { method: 'GET', path: '/', defaultHeaders: {}, defaultBody: {} };
      function openModalAndSend(onSend){
        const modal = ensureModal(); modal.style.display='flex';
        const hEl = modal.querySelector('#req-headers'); const bEl = modal.querySelector('#req-body');
        hEl.value = JSON.stringify(reqContext.defaultHeaders||{}, null, 2);
        bEl.value = JSON.stringify(reqContext.defaultBody||{}, null, 2);
        const sendBtn = modal.querySelector('#req-send');
        const handler = async ()=>{
          try{
            const headers = JSON.parse(hEl.value||'{}');
            const body = JSON.parse(bEl.value||'{}');
            await onSend(headers, body);
            modal.style.display='none';
          }catch(e){ showToastSafe('JSON 解析失败: '+e.message, 'error'); }
        };
        sendBtn.addEventListener('click', handler, { once: true });
      }

      // 将按钮就近渲染到最近的标题下
      try{
        const out = document.getElementById('api-full-out'); // 可能由之前步骤创建
        const headersList = el.querySelectorAll('h1, h2, h3');
        const lines = md.split(/\n/);
        const re = /^\s*-\s*`(GET|POST|PUT|DELETE)\s+([^`]+)`/i;
        const items = [];
        for(const line of lines){ const m = re.exec(line); if(m){ items.push({method:m[1].toUpperCase(), path:m[2].trim(), raw: line}); } }
        const whitelist = new Set([
          '/health','/scripts','/api/security/rbac','/api/scheduler/circuit','/api/status','/api/modules','/api/pipeline/validate','/api/generate','/api/pipeline/run','/api/docs/sync','/api/docs/propose'
        ]);
        const minimalBodies = {
          '/api/pipeline/validate': { nodes: [ { id: 'n1', script: 'demo', params: {} } ] },
          '/api/generate': { model: 'gpt-oss:mini', prompt: 'ping', stream: false }
          ,'/api/pipeline/run': { nodes: [ { id: 'n1', script: 'demo', params: {} } ], max_concurrency: 1 },
          '/api/docs/sync': { id: 'API_FULL', content: '同步占位内容', target: 'frontend/pages' },
          '/api/docs/propose': { id: 'API_FULL', changes: [ { op: 'append', content: '追加占位段落' } ] }
        };
        const safeItems = items.filter(i=> whitelist.has(i.path));
        // 映射：找到每个条目的最近标题节点
        // 改为基于文档结构位置：找到端点所在段落的前一个标题
        // 构建行到元素的粗略映射：通过渲染后的 HTML 搜索端点文本出现位置的父块，回溯到最近的 h2/h3
        function findNearestHeaderForPath(path){
          const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
          let textNode, header;
          while((textNode = walker.nextNode())){
            if((textNode.nodeValue||'').indexOf(path) !== -1){
              // 回溯到最近的元素块
              let cur = textNode.parentNode;
              while(cur && cur !== el){
                if(/^H[123]$/.test(cur.tagName||'')) { header = cur; break; }
                cur = cur.previousElementSibling || cur.parentNode;
              }
              if(header) break;
            }
          }
          return header || headersList[0];
        }
        safeItems.forEach(it=>{
          let targetHeader = findNearestHeaderForPath(it.path);
          const wrap = document.createElement('div'); wrap.style.display='inline-flex'; wrap.style.gap='8px'; wrap.style.marginLeft='8px';
          const btn = document.createElement('button'); btn.className='menu-item'; btn.textContent = `${it.method} ${it.path}`;
          // 预设选择下拉
          const presetSel = document.createElement('select'); presetSel.className='menu-item'; presetSel.style.border='1px solid #334155'; presetSel.style.background='#0b1220'; presetSel.style.color='#e2e8f0';
          const presets = [{name:'默认',key:'default'}]; if(minimalBodies[it.path]) presets.push({name:'最小样例',key:'minimal'});
          presets.forEach(p=>{ const o=document.createElement('option'); o.value=p.key; o.textContent=p.name; presetSel.appendChild(o); });
          btn.addEventListener('click', async ()=>{
            try{
              const headers = {}; try{ const mod=await import('/static/js/auth.js'); Object.assign(headers, mod.auth.getAuthHeaders?.()||{}); }catch(_){ }
              let opts = { method: it.method, headers };
              if(it.method !== 'GET'){
                const preset = presetSel.value==='minimal' ? (minimalBodies[it.path]||{}) : {};
                reqContext.method = it.method; reqContext.path = it.path; reqContext.defaultHeaders = headers; reqContext.defaultBody = preset;
                openModalAndSend(async (hdrs, body)=>{
                  const res = await fetch(it.path, { method: it.method, headers: { 'Content-Type':'application/json', ...hdrs }, body: JSON.stringify(body) });
                  const text = await res.text(); const outEl = document.getElementById('api-full-out'); if(outEl){ try{ outEl.textContent = JSON.stringify(JSON.parse(text), null, 2); }catch{ outEl.textContent = text; } }
                  // 简单 schema 断言：检测常见结构键
                  try{
                    const j = JSON.parse(text);
                    const statusOk = res.ok;
                    const baseOk = ['code','data','error'].some(k=> Object.prototype.hasOwnProperty.call(j||{}, k));
                    // 端点特定校验
                    let endpointOk = true;
                    if(it.path === '/health'){
                      endpointOk = j && j.code === 0 && j.data && typeof j.data.status === 'string';
                    }
                    if(it.path === '/api/pipeline/validate'){
                      endpointOk = j && (j.code === 0 || (j.code === 1 && Array.isArray(j.errors)));
                    }
                    if(it.path === '/api/pipeline/run'){
                      endpointOk = j && j.code === 0 && j.task_id;
                    }
                    if(it.path === '/api/docs/propose'){
                      endpointOk = j && j.code === 0;
                    }
                    const verdict = statusOk && baseOk && endpointOk ? '通过' : '需排查';
                    showToastSafe(`请求完成 ${res.status} ｜ 结构校验：${verdict}`, statusOk?'info':'warn');
                    // 记录摘要
                    try{ const sumEl = document.getElementById('api-validate-summary'); const listEl = document.getElementById('api-validate-list'); if(sumEl){ const cur = sumEl.textContent||''; } if(listEl){ const prev = listEl.innerHTML||''; listEl.innerHTML = prev + `<div>${it.path} ｜ 状态 ${res.status} ｜ 结论 ${verdict}</div>`; const pass = (listEl.innerText.match(/结论 通过/g)||[]).length; const total = (listEl.innerText.match(/结论 /g)||[]).length; if(sumEl){ sumEl.textContent = `本次演练通过 ${pass}/${total}`; } } }catch(_){ }
                  }catch(_){ showToastSafe('请求完成: '+res.status, res.ok?'info':'warn'); }
                });
                return;
              }else{
                const res = await fetch(it.path, opts);
                const text = await res.text(); const outEl = document.getElementById('api-full-out'); if(outEl){ try{ outEl.textContent = JSON.stringify(JSON.parse(text), null, 2); }catch{ outEl.textContent = text; } }
                try{
                  const j = JSON.parse(text);
                  const statusOk = res.ok;
                  const baseOk = ['code','data','error'].some(k=> Object.prototype.hasOwnProperty.call(j||{}, k));
                  let endpointOk = true;
                  if(it.path === '/health'){
                    endpointOk = j && j.code === 0 && j.data && typeof j.data.status === 'string';
                  }
                  const verdict = statusOk && baseOk && endpointOk ? '通过' : '需排查';
                  showToastSafe(`请求完成 ${res.status} ｜ 结构校验：${verdict}`, statusOk?'info':'warn');
                }catch(_){ showToastSafe('请求完成: '+res.status, res.ok?'info':'warn'); }
              }
            }catch(err){ const outEl = document.getElementById('api-full-out'); if(outEl) outEl.textContent = String(err.message||err); showToastSafe('请求失败','error'); }
          });
          wrap.appendChild(btn);
          wrap.appendChild(presetSel);
          targetHeader && targetHeader.parentNode && targetHeader.parentNode.insertBefore(wrap, targetHeader.nextSibling);
        });
      }catch(_){ }
      // 从文档提取端点并渲染一键演练
      try{
        const epCard = document.createElement('div'); epCard.className='card';
        epCard.innerHTML = '<h3>示例端点一键演练</h3><div id="api-full-quick" style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px"></div><pre id="api-full-out" style="min-height:120px"></pre>';
        el.parentNode.insertBefore(epCard, el.nextSibling);
        const quick = document.getElementById('api-full-quick'); const out = document.getElementById('api-full-out');
        const summaryCard = document.createElement('div'); summaryCard.className='card'; summaryCard.innerHTML = '<h3>校验摘要</h3><div id="api-validate-summary" class="small">尚未演练</div><div id="api-validate-list" class="small" style="margin-top:6px"></div>';
        epCard.parentNode.insertBefore(summaryCard, epCard.nextSibling);
        const verdictLog = [];
        const lines = md.split(/\n/);
        const re = /^\s*-\s*`(GET|POST|PUT|DELETE)\s+([^`]+)`/i;
        const endpoints = [];
        for(const line of lines){ const m = re.exec(line); if(m){ endpoints.push({method:m[1].toUpperCase(), path:m[2].trim()}); } }
        const whitelist = new Set(['/health','/scripts','/api/security/rbac','/api/scheduler/circuit','/api/status','/api/modules']);
        const safe = endpoints.filter(e=> whitelist.has(e.path));
        safe.forEach(e=>{
          const btn = document.createElement('button'); btn.className='menu-item'; btn.textContent = `${e.method} ${e.path}`;
          btn.addEventListener('click', async ()=>{
            try{
              const headers = {}; try{ const mod=await import('/static/js/auth.js'); Object.assign(headers, mod.auth.getAuthHeaders?.()||{}); }catch(_){}
              const res = await fetch(e.path, { method: e.method, headers });
              const text = await res.text(); try{ out.textContent = JSON.stringify(JSON.parse(text), null, 2); }catch{ out.textContent = text; }
              // 记录 GET 请求的简单校验（基础键存在）
              try{ const j = JSON.parse(text); const baseOk = ['code','data','error'].some(k=> Object.prototype.hasOwnProperty.call(j||{}, k)); const verdict = res.ok && baseOk ? '通过' : '需排查'; verdictLog.push({ path: e.path, status: res.status, verdict }); }catch(_){ verdictLog.push({ path: e.path, status: res.status, verdict: res.ok?'通过':'需排查' }); }
              const pass = verdictLog.filter(v=>v.verdict==='通过').length; const total = verdictLog.length;
              const sumEl = document.getElementById('api-validate-summary'); if(sumEl){ sumEl.textContent = `本次演练通过 ${pass}/${total}`; }
              const listEl = document.getElementById('api-validate-list'); if(listEl){ listEl.innerHTML = verdictLog.map(v=>`<div>${v.path} ｜ 状态 ${v.status} ｜ 结论 ${v.verdict}</div>`).join(''); }
              showToastSafe('请求完成: '+res.status, res.ok?'info':'warn');
            }catch(err){ out.textContent = String(err.message||err); showToastSafe('请求失败','error'); }
          });
          quick.appendChild(btn);
        });
        if(safe.length===0){ const hint=document.createElement('div'); hint.className='small'; hint.textContent='未检测到安全端点，已跳过渲染'; quick.appendChild(hint); }
      }catch(_){ }
      // 构建 TOC
      try{
        const toc = document.getElementById('api-full-toc'); if(toc){
          const headers = el.querySelectorAll('h2, h3');
          toc.innerHTML = Array.from(headers).map(h=>`<a href="#${h.id}" class="toc-link" style="margin-right:8px">${h.textContent}</a>`).join('');
          // 平滑滚动绑定
          toc.addEventListener('click', (e)=>{
            const a = e.target.closest('a.toc-link'); if(!a) return;
            e.preventDefault();
            const id = a.getAttribute('href').slice(1);
            const target = el.querySelector('#'+CSS.escape(id));
            if(target){ try{ target.scrollIntoView({ behavior:'smooth', block:'start' }); }catch(_){ location.hash = a.getAttribute('href'); } }
          });
        }
      }catch(_){ }
      // 复制按钮绑定
      try{
        el.querySelectorAll('.copybtn').forEach(btn=>{
          btn.addEventListener('click', async ()=>{
            const raw = decodeURIComponent(btn.dataset.code||'');
            try{ await navigator.clipboard.writeText(raw); showToastSafe('已复制到剪贴板','info'); }
            catch(e){ showToastSafe('复制失败: '+e.message,'error'); }
          });
        });
      }catch(_){ }
    }).catch(e=>{
      const el=document.getElementById('api-full-view'); if(el) el.textContent=String(e);
    });
  }catch(_){ }
}

function bindQuickPlay(){
  const outH = $('out-health'); const outS = $('out-scripts'); const outR = $('out-rbac'); const outC = $('out-circuit');
  const safeOut = (el, data)=>{ if(!el) return; el.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2); };
  $('btn-health')?.addEventListener('click', async ()=>{ try{ const d=await fetchJSON('/health'); safeOut(outH,d);}catch(e){ showToastSafe(e.message,'error'); }});
  $('btn-scripts')?.addEventListener('click', async ()=>{ try{ const d=await fetchJSON('/scripts'); safeOut(outS,d);}catch(e){ showToastSafe(e.message,'error'); }});
  $('btn-health-retry')?.addEventListener('click', async ()=>{ try{ const d=await fetchJSON('/health'); safeOut(outH,d);}catch(e){ showToastSafe(e.message,'error'); }});
  $('btn-scripts-retry')?.addEventListener('click', async ()=>{ try{ const d=await fetchJSON('/scripts'); safeOut(outS,d);}catch(e){ showToastSafe(e.message,'error'); }});
  $('btn-rbac')?.addEventListener('click', async ()=>{ try{ const d=await fetchJSON('/api/security/rbac'); safeOut(outR,d);}catch(e){ showToastSafe(e.message,'error'); }});
  $('btn-circuit')?.addEventListener('click', async ()=>{ try{ const d=await fetchJSON('/api/scheduler/circuit'); safeOut(outC,d);}catch(e){ showToastSafe(e.message,'error'); }});
}

// Audit integration: load hx-report and render bubbles + progress
async function loadHxReport(){
  try {
    const res = await fetch('/logs/hx-report.json');
    const text = await res.text();
    const data = (()=>{ try{ return JSON.parse(text); }catch{ return {}; } })();
    renderHxSummary(data);
    renderHxBubbles(data);
    renderHxProgress(data);
  } catch (e) {
    showToastSafe('读取审计报告失败: ' + e.message, 'error');
  }
}

function renderHxSummary(data){
  const el = document.getElementById('ap-hx-summary'); if(!el) return;
  try{
    const pages = data?.pages || [];
    const okCount = pages.filter(p=> String(p.code||'') === '200').length;
    const total = pages.length;
    const modulesOk = (data?.modules_policy?.violations||[]).length === 0;
    const htmlOk = (data?.html_policy?.violations||[]).length === 0;
    el.textContent = `页面可用 ${okCount}/${total} ｜ 模块策略${modulesOk?'通过':'有违规'} ｜ HTML内联${htmlOk?'通过':'有违规'}`;
  }catch(_){ el.textContent='（无摘要）'; }
}

function renderHxBubbles(data){
  const grid = document.getElementById('ap-hx-bubbles'); if(!grid) return; grid.innerHTML='';
  const bubbles = data?.bubbles || data?.events || [];
  const list = Array.isArray(bubbles) ? bubbles.slice(0,50) : [];
  list.forEach(b=>{
    const item=document.createElement('div'); item.className='module-item';
    const t = (b.time||b.ts||'').toString().replace('T',' ').slice(0,19);
    item.innerHTML = `<span>${t}</span><span>${b.type||b.event||'event'}</span><span style="color:#93c5fd">${(b.detail||b.message||'').slice(0,60)}</span>`;
    grid.appendChild(item);
  });
}

function renderHxProgress(data){
  const el = document.getElementById('api-progress'); const el2 = document.getElementById('ap-hx-progress');
  const target = el2 || el; if(!target) return; target.innerHTML='';
  const progress = data?.progress || { done: 0, total: 0 };
  const done = Number(progress.done||0); const total = Number(progress.total||0) || 1;
  const pct = Math.round((done/total)*100);
  const bar=document.createElement('div'); bar.style.height='16px'; bar.style.background='#0f172a'; bar.style.border='1px solid #334155'; bar.style.borderRadius='999px'; bar.style.overflow='hidden';
  const fill=document.createElement('div'); fill.style.width=pct+'%'; fill.style.height='100%'; fill.style.background='#1df0ff'; fill.style.transition='width 0.3s';
  bar.appendChild(fill); target.appendChild(bar);
  const text=document.createElement('div'); text.style.marginTop='6px'; text.style.color='#93c5fd'; text.textContent=`完成度：${done}/${total}（${pct}%）`;
  target.appendChild(text);
}

function bindHxActions(){
  document.getElementById('ap-load-hx')?.addEventListener('click', loadHxReport);
  document.getElementById('ap-refresh-hx')?.addEventListener('click', async ()=>{ try{ await fetch('/api/audit/refresh',{method:'POST'}); }catch(_){ } loadHxReport(); });
}

function bindPlaceholders(){
  document.addEventListener('click', async (e)=>{
    const btn = e.target.closest('button.menu-item[data-ph]'); if(!btn) return;
    const t = btn.dataset.ph; const out = $('ap-ph-out'); if(!out) return;
    try{
      const d = await fetchJSON(`/api/placeholder/${t}`);
      out.textContent = typeof d === 'string' ? d : JSON.stringify(d, null, 2);
    }catch(err){ out.textContent = String(err.message||err); }
  });
}

async function init(){
  // Ensure required containers exist when HTML is minimal
  try{
    if(!document.getElementById('topbar')){
      const h = document.createElement('header'); h.id = 'topbar'; h.className='topbar';
      (document.body || document.documentElement).insertBefore(h, (document.body||document.documentElement).firstChild);
    }
    if(!document.getElementById('api-doc-root')){
      const main = document.querySelector('main') || document.createElement('main');
      if(!main.parentNode){ (document.body||document.documentElement).appendChild(main); }
      const sec = document.createElement('section'); sec.id='api-doc-root'; sec.className='main-content';
      main.appendChild(sec);
    }
  }catch(_){ }
  renderTopbar();
  renderSections();
  bindQuickPlay();
  bindPlaceholders();
  bindHxActions();
  startHealthLoop();
  try{ const root=document.getElementById('api-doc-root'); if(root){ root.style.opacity='1'; } }catch(_){ }
}

document.readyState==='loading' ? document.addEventListener('DOMContentLoaded', init) : init();
// 取消入口守卫：允许直接访问；仍读取共享配置（若存在）
try{
  var shared = localStorage.getItem('yl_shared_config');
  if(shared){ try{ window.AP_SHARED = JSON.parse(shared); }catch(e){} }
}catch(e){ /* ignore */ }

// 冒泡点击激活效果（作用域选择器，避免影响其他元素）
(function () {
  var bubblesWrap = document.getElementById('ap-bubbles');
  if (bubblesWrap) {
    bubblesWrap.addEventListener('click', function (e) {
      var el = e.target.closest('.ap-bubble');
      if (!el) return;
      if (el.classList.contains('active')) { el.classList.remove('active'); } else { el.classList.add('active'); }
    });
  }
})();

// 占位接口演练：统一通过 /api 代理
(function(){
  var out = document.getElementById('ap-ph-out');
  function call(key){
    fetch('/api/placeholder/'+key).then(function(r){ return r.json(); }).then(function(j){
      out.textContent = JSON.stringify(j, null, 2);
    }).catch(function(e){ out.textContent = String(e); });
  }
  Array.from(document.querySelectorAll('[data-ph]')).forEach(function(btn){
    btn.addEventListener('click', function(){ call(btn.getAttribute('data-ph')); });
  });
})();

// 注入右上角登录状态徽标（纯 JS，不改 HTML）
(async function(){ try{ const mod=await import('/static/js/auth.js'); const role=localStorage.getItem('yl_user_role')||'user'; const wrap=document.createElement('div'); wrap.style.position='fixed'; wrap.style.top='14px'; wrap.style.right='14px'; wrap.style.zIndex='9999'; wrap.style.display='flex'; wrap.style.gap='8px'; const badge=document.createElement('div'); badge.style.padding='6px 10px'; badge.style.borderRadius='999px'; badge.style.fontSize='12px'; badge.style.background='#0a0f1e'; badge.style.color='#1de9b6'; badge.style.border='1px solid rgba(29,240,255,0.35)'; const acc=(mod.auth.getUser?.() && mod.auth.getUser().account)||''; badge.textContent=`已登录：${acc||'用户'}｜角色：${role}`; const exit=document.createElement('button'); exit.textContent='退出登录'; exit.className='btn'; exit.style.padding='6px 10px'; exit.style.borderRadius='999px'; exit.style.background='#ef4444'; exit.style.color='#fff'; exit.style.border='none'; exit.style.cursor='pointer'; exit.onclick=()=>{ try{ (mod.auth.clearToken?.()||mod.auth.setToken?.('')); }catch(_){ } try{ localStorage.removeItem('yl_user_role'); }catch(_){ } window.location.href='/pages/login.html'; }; wrap.appendChild(badge); wrap.appendChild(exit); document.body.appendChild(wrap);}catch(_){ } })();

// 从后端拉取脚本清单，渲染模块卡片 + 快捷操作
(function(){
  function renderModuleCard(name){
    var el = document.createElement('div');
    el.className = 'card';
    el.innerHTML = [
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">',
      '<div style="font-weight:700;color:#111827">'+name+'</div>',
      '<div style="font-size:12px;color:#6b7280;border:1px solid #e5e7eb;border-radius:999px;padding:2px 8px">脚本</div>',
      '</div>',
      '<div style="display:flex;gap:8px;margin-bottom:8px">',
      '<div style="flex:1;background:#f9fafb;border:1px dashed #e5e7eb;border-radius:8px;padding:8px"><b>文件：</b>'+name+'.py</div>',
      '<div style="flex:1;background:#f9fafb;border:1px dashed #e5e7eb;border-radius:8px;padding:8px"><b>接口：</b>/api/'+name+'</div>',
      '</div>',
      '<div style="display:flex;gap:8px">',
      '<button class="menu-item" data-action="run" style="background:#2563eb;color:#fff">快速运行</button>',
      '<button class="menu-item" data-action="status">查看状态</button>',
      '</div>'
    ].join('');
    return el;
  }
  function renderModules(list){
    var host = document.getElementById('ap-modules-list');
    if(!host) return; host.innerHTML = '';
    if (host) { list.forEach(function(n){ host.appendChild(renderModuleCard(n)); }); }
    if(window.ModulesBind){ window.ModulesBind(host); }
  }
  function load(){
    fetch('/scripts').then(function(r){ return r.json(); }).then(function(j){
      if(j && j.code === 0 && Array.isArray(j.data)){
        renderModules(j.data);
        return;
      }
      throw new Error('fallback');
    }).catch(function(){
      import('/static/js/modules.js').then(function(mod){
        var apiModules = mod.apiModules; var bindQuickActions = mod.bindQuickActions;
        window.ModulesBind = bindQuickActions;
        apiModules().then(function(list){ renderModules(list||[]); });
      }).catch(function(){ /* 静默失败 */ });
    });
  }
  document.addEventListener('DOMContentLoaded', load);
})();

// 健康检查与脚本清单按钮交互
(function(){
  function setText(id, value){ var el = document.getElementById(id); if(el){ el.textContent = value; } }
  function toast(msg, type){
    try{
      var el = document.createElement('div');
      el.style.position='fixed'; el.style.right='16px'; el.style.top='16px'; el.style.zIndex='9999';
      el.style.padding='8px 12px'; el.style.borderRadius='8px'; el.style.color='#fff';
      el.style.background = type==='error'? '#ef4444' : (type==='warn' ? '#f59e0b' : '#10b981');
      el.style.boxShadow='0 6px 16px rgba(0,0,0,0.15)';
      el.textContent = msg;
      if (document.body) document.body.appendChild(el);
      setTimeout(function(){ try{ document.body.removeChild(el); }catch(_){} }, 1800);
    }catch(_){ }
  }
  function jsonOut(id, obj){ setText(id, JSON.stringify(obj, null, 2)); }
  function wire(){
    var b1 = document.getElementById('btn-health');
    var b2 = document.getElementById('btn-scripts');
    var r1 = document.getElementById('btn-health-retry');
    var r2 = document.getElementById('btn-scripts-retry');
    var all = document.getElementById('btn-all');
    var br = document.getElementById('btn-rbac');
    var bc = document.getElementById('btn-circuit');
    async function fetchWithTimeout(url, ms){
      var ctrl = new AbortController(); var id = setTimeout(function(){ ctrl.abort(); }, ms);
      // 统一带鉴权头
      let headers={};
      try{ const mod=await import('/static/js/auth.js'); headers = mod.auth.getAuthHeaders?.() || {}; }catch(_){ }
      return fetch(url, { signal: ctrl.signal, headers }).finally(function(){ clearTimeout(id); });
    }
    if(b1){ b1.addEventListener('click', function(){ fetchWithTimeout('/health', 2500).then(function(r){ if(!r.ok){ throw new Error('HTTP '+r.status); } return r.json(); }).then(function(j){ jsonOut('out-health', j); toast('健康检查成功','success'); }).catch(function(e){ setText('out-health', String(e)); toast('健康检查失败: '+e,'error'); }); }); }
    if(b2){ b2.addEventListener('click', function(){ fetchWithTimeout('/scripts', 2500).then(function(r){ if(!r.ok){ throw new Error('HTTP '+r.status); } return r.json(); }).then(function(j){ jsonOut('out-scripts', j); toast('脚本清单获取成功','success'); }).catch(function(e){ setText('out-scripts', String(e)); toast('脚本清单获取失败: '+e,'error'); }); }); }
    if(r1){ r1.addEventListener('click', function(){ b1 && b1.click(); }); }
    if(r2){ r2.addEventListener('click', function(){ b2 && b2.click(); }); }
    if(all){
      all.addEventListener('click', async function(){
        toast('开始全部探测…','warn');
        try{
          const h = await fetchWithTimeout('/health', 3000); if(!h.ok) throw new Error('health HTTP '+h.status);
          const hj = await h.json(); jsonOut('out-health', hj);
          const s = await fetchWithTimeout('/scripts', 3000); if(!s.ok) throw new Error('scripts HTTP '+s.status);
          const sj = await s.json(); jsonOut('out-scripts', sj);
          const r = await fetchWithTimeout('/api/security/rbac', 3000); if(!r.ok) throw new Error('rbac HTTP '+r.status);
          const rj = await r.json(); jsonOut('out-rbac', rj);
          const c = await fetchWithTimeout('/api/scheduler/circuit', 3000); if(!c.ok) throw new Error('circuit HTTP '+c.status);
          const cj = await c.json(); jsonOut('out-circuit', cj);
          toast('全部探测完成','success');
        }catch(e){ toast('全部探测失败: '+e,'error'); }
      });
    }
    if(br){ br.addEventListener('click', function(){ fetchWithTimeout('/api/security/rbac', 2500).then(r=>r.json()).then(j=>jsonOut('out-rbac', j)).catch(e=>setText('out-rbac', String(e))); }); }
    if(bc){ bc.addEventListener('click', function(){ fetchWithTimeout('/api/scheduler/circuit', 2500).then(r=>r.json()).then(j=>jsonOut('out-circuit', j)).catch(e=>setText('out-circuit', String(e))); }); }
    try{
      var p = new URLSearchParams(window.location.search);
      var action = p.get('action');
      if(action === 'health' && b1){ b1.click(); }
      if(action === 'scripts' && b2){ b2.click(); }
      if(action === 'all'){
        (async function(){
          if(b1){ b1.click(); await new Promise(r=>setTimeout(r, 400)); }
          if(b2){ b2.click(); }
        })();
      }
    }catch(_){ }
  }
  document.addEventListener('DOMContentLoaded', wire);
})();

// LayUI 进度条初始化
(function () {
  var init = function () { try { layui && layui.element && layui.element.render('progress', 'apProgressDemo'); } catch (_) { } };
  if (window.layui) { init(); }
  else { window.addEventListener('DOMContentLoaded', init); }
})();

// 框架总览（六项卡片）内置数据 + 渲染
(function () {
  var data = [
    { id: 'param_deploy', name: '参数部署', frontend: 'index → 参数部署', backend: 'GET/POST /params/*', progress: 30, bubble: '统一参数编辑/校验/下发占位已呈现；后端接口待接入', desc: '统一参数编辑/校验/下发占位已呈现；后端接口待接入', done: false },
    { id: 'smart-schedule', name: '智能调度', frontend: 'index → 智能调度', backend: 'POST /scheduler/*, GET /scheduler/status', progress: 20, bubble: '启动/停止/状态接口待联通', desc: '启停与限流策略占位说明完成；后端排期中', done: false },
    { id: 'collect-task', name: '采集任务', frontend: 'index → 采集任务', backend: 'GET/POST /collect/*', progress: 25, bubble: '任务列表与创建接口需联通', desc: '列表/创建/校验/详情/启动/停止流程占位已呈现', done: false },
    { id: 'enum-task', name: '枚举任务', frontend: 'index → 枚举任务', backend: 'GET /enum/tasks, POST /enum/run', progress: 15, bubble: 'BIN校验与枚举触发待接入', desc: '字典/规则驱动枚举说明完成', done: false },
    { id: 'recognize-task', name: '识别任务', frontend: 'index → 识别任务', backend: 'POST /recognize/submit, GET /recognize/status/*', progress: 10, bubble: '只读查看流程占位完成，接口待通', desc: '提交、状态、路由追踪、DNS/ASN等说明完成', done: false },
    { id: 'crack-task', name: '破解任务', frontend: 'index → 破解任务', backend: 'POST /crack/*', progress: 10, bubble: '多类破解接口清单已列出', desc: '验证码/URL/ZIP/账号逻辑/B64/清除打码等', done: false },
    { id: 'status', name: '自动化状态', frontend: 'index → 自动化状态', backend: 'GET /auto/*', progress: 20, bubble: '总况与进度聚合待拉通', desc: '安全级别、快速任务说明完成', done: false },
    { id: 'log', name: '日志管理', frontend: 'index → 日志管理', backend: 'GET /logs/*, DELETE /logs/cleanup', progress: 20, bubble: '各类日志查询与清理待接入', desc: '部署/安装/登录/使用日志说明完成', done: false },
    { id: 'workflow-deploy', name: '工作流部署', frontend: 'index → 工作流部署', backend: 'GET/POST /workflow/*', progress: 15, bubble: '部署/回滚/开关待联通', desc: '编排与版本管理占位完成', done: false },
    { id: 'ai-advanced', name: 'AI高级联动', frontend: 'index → AI高级联动', backend: 'POST /ai/multimodel/*', progress: 25, bubble: '编排运行与召回优化接口待通', desc: '六大板块说明完成', done: false },
    { id: 'cross-parse', name: '交叉解析', frontend: 'index → 交叉解析', backend: 'POST /parse/cross, GET /parse/cross/*', progress: 15, bubble: '多源数据对齐与冲突消解流程待接入', desc: '发起解析、结果与一致性校验占位完成', done: false },
    { id: 'anti-trace', name: '反追反穿', frontend: 'index → 反追反穿', backend: 'POST /security/hardening, GET /security/checklist', progress: 20, bubble: '自防合规清单与加固接口就绪', desc: '合法自检与工具提示完成', done: false },
    { id: 'extreme-break', name: '极限突破', frontend: 'index → 极限突破', backend: 'POST/GET /stress/sandbox/*', progress: 10, bubble: '沙箱压测流程待对接', desc: '策略演练占位', done: false },
    { id: 'decode-challenge', name: '破译挑战', frontend: 'index → 破译挑战', backend: 'POST /decode/submit, GET /decode/result/*', progress: 10, bubble: '提交与结果查询入口就绪', desc: '复杂编码/混淆场景占位', done: false },
    { id: 'auth', name: '权限管理', frontend: 'index → 权限管理', backend: 'GET /auth/users, POST /auth/roles, POST /auth/perms/bind', progress: 35, bubble: '基础权限接口清单已确定', desc: '权限配置与审计说明完成', done: false },
    { id: 'api-doc', name: 'API 文档', frontend: 'index → API接口文档；docs.html', backend: 'GET /api/docs/API', progress: 50, bubble: '文档视图已部署', desc: '统一接口文档渲染可用', done: true },
    { id: 'prod-control', name: '后端控制', frontend: 'index → 后端控制；跳转 monitor.html', backend: 'GET /health, GET /api/status', progress: 30, bubble: '监控大屏已部署', desc: '后端健康泡泡占位', done: false },
    { id: 'ai-train', name: 'AI训练', frontend: 'index → AI训练', backend: 'POST /train/*, GET /train/status/*, POST /dataset/import', progress: 10, bubble: '训练任务接口待接入', desc: '训练/指标/数据集占位', done: false },
    { id: 'fastapi-control', name: 'FastAPI联动', frontend: 'index → FastAPI服务联动', backend: 'POST /fastapi/*, GET /fastapi/*', progress: 15, bubble: '启停与路由同步接口待联通', desc: '健康检查与路由同步说明完成', done: false }
  ];
  function card(it) {
    var el = document.createElement('div');
    el.className = 'card';
    el.innerHTML = [
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">' +
      '<div style="font-weight:700;color:#111827">' + it.name + '</div>' +
      '<div style="font-size:12px;color:#6b7280;border:1px solid #e5e7eb;border-radius:999px;padding:2px 8px">' + it.id + '</div>' +
      '</div>',
      '<div style="display:flex;gap:8px;margin-bottom:8px">' +
      '<div style="flex:1;background:#f9fafb;border:1px dashed #e5e7eb;border-radius:8px;padding:8px"><b>前端映射：</b>' + it.frontend + '</div>' +
      '<div style="flex:1;background:#f9fafb;border:1px dashed #e5e7eb;border-radius:8px;padding:8px"><b>后端接口：</b>' + it.backend + '</div>' +
      '</div>',
      '<div style="height:8px;background:#e5e7eb;border-radius:999px;overflow:hidden;margin-bottom:6px"><div class="ap-progress-anim" style="height:100%;background:linear-gradient(90deg,#2563eb,#93c5fd);width:' + it.progress + '%"></div></div>',
      '<div style="font-size:12px;color:#6b7280;">冒泡检测：' + it.bubble + '</div>',
      '<div style="font-size:13px;color:#374151;">部署内容说明：' + it.desc + '</div>',
      '<div style="display:flex;justify-content:space-between;color:#6b7280;font-size:12px;margin-top:4px">' +
      '<span>部署同步百分比进度：<b style="color:#111827">' + it.progress + '%</b></span>' +
      '<span style="color:' + (it.done ? '#16b777' : '#f59e0b') + '">是否完成：' + (it.done ? '已完成' : '未完成') + '</span>' +
      '</div>'
    ].join('');
    el.style.cursor = 'pointer';
    el.addEventListener('click', function () {
      var more = el.querySelector('.fw-more');
      if (more) { more.remove(); return; }
      var m = document.createElement('div');
      m.className = 'fw-more';
      m.style = 'margin-top:8px; background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:8px; color:#374151;';
      m.innerHTML = '<div style="font-size:12px;color:#6b7280;">端点演练示例：</div><pre style="margin:6px 0; white-space:pre-wrap">GET ' + (it.backend.split(',')[0] || '') + '\nPOST ' + (it.backend.split(',')[1] || '') + '</pre>';
      if (el) el.appendChild(m);
    });
    return el;
  }
  function render() {
    var grid = document.getElementById('ap-framework-grid');
    if (!grid) return; grid.innerHTML = '';
    var list = data.slice();
    var q = (document.getElementById('ap-fw-filter')?.value || '').trim().toLowerCase();
    if (q) {
      list = list.filter(function (it) {
        return [it.id, it.name, it.frontend, it.backend, it.desc, it.bubble].some(function (s) { return String(s).toLowerCase().includes(q); });
      });
    }
    var sort = document.getElementById('ap-fw-sort')?.value || 'none';
    if (sort === 'progress-desc') { list.sort(function (a, b) { return b.progress - a.progress; }); }
    else if (sort === 'progress-asc') { list.sort(function (a, b) { return a.progress - b.progress; }); }
    else if (sort === 'done') { list.sort(function (a, b) { return (b.done === true) - (a.done === true) || (b.progress - a.progress); }); }
    if (grid) { list.forEach(function (it) { grid.appendChild(card(it)); }); }
  }
  document.addEventListener('DOMContentLoaded', function () {
    render();
    var f = document.getElementById('ap-fw-filter'); var s = document.getElementById('ap-fw-sort');
    f && f.addEventListener('input', render);
    s && s.addEventListener('change', render);
  });
})();

// 统一接口测试面板
(function () {
  var main = document.getElementById('main-content');
  var panel = document.createElement('div');
  panel.className = 'card';
  panel.innerHTML = [
    '<div style="font-weight:800;color:#10b981;margin-bottom:6px;display:flex;gap:8px;align-items:center">🧪 接口测试面板</div>',
    '<div class="flex-row" style="gap:8px;align-items:flex-start;margin-bottom:10px">',
    '<select id="ap-test-method" class="menu-item" style="border:1px solid #e5e7eb;background:#fff">',
    '<option>GET</option><option>POST</option>',
    '</select>',
    '<input id="ap-test-path" class="menu-item" style="flex:1;border:1px solid #e5e7eb;background:#fff" placeholder="接口路径（如 /backend/health 或 /collect/tasks）" />',
    '<button id="ap-test-send" class="menu-item" style="background:#2563eb;color:#fff">发送</button>',
    '</div>',
    '<textarea id="ap-test-body" rows="6" style="width:100%;border:1px solid #e5e7eb;border-radius:8px;padding:8px" placeholder="参数模板（JSON），GET 可留空。例如：{\n  \"keyword\": \"demo\"\n}"></textarea>',
    '<div class="flex-row" style="gap:8px;margin-top:8px">',
    '<button id="ap-test-load-sample" class="menu-item" style="background:#f59e0b;color:#1f2937">加载示例入参</button>',
    '<span class="small-muted">示例来自已知常用端点</span>',
    '</div>',
    '<pre id="ap-test-result" class="log-box" style="margin-top:10px;height:220px"></pre>'
  ].join('');
  if (main) main.appendChild(panel);

  var samples = {
    '/backend/health': {},
    '/backend/status': {},
  };
  (function buildSamplesFromDoc() {
    var docPath = './docs/../api_playground/前后端统一接口api文档.md';
    var fallbackPaths = [
      './前后端统一接口api文档.md',
      '../api_playground/前后端统一接口api文档.md'
    ];
    function tryFetch(paths, i) {
      if (i >= paths.length) return Promise.reject('doc not found');
      return fetch(paths[i]).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); })
        .catch(function () { return tryFetch(paths, i + 1); });
    }
    tryFetch([docPath].concat(fallbackPaths), 0).then(function (text) {
      var lines = text.split(/\r?\n/);
      var currentMethod = null, currentPath = null;
      for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim();
        var m = line.match(/^[-*]\s*(GET|POST)\s+`([^`]+)`/i);
        if (m) { currentMethod = m[1].toUpperCase(); currentPath = m[2]; continue; }
        var p = line.match(/^-\s*入参：`?\{(.+)\}`?/);
        if (currentPath && p) {
          try {
            var jsonStr = '{' + p[1] + '}';
            jsonStr = jsonStr.replace(/([,{\s])([a-zA-Z_][\w-]*)\s*:/g, '$1"$2":');
            jsonStr = jsonStr.replace(/'([^']*)'/g, '"$1"');
            var obj = JSON.parse(jsonStr);
            if (currentMethod === 'POST') { samples[currentPath] = obj; } else { samples[currentPath] = samples[currentPath] || {}; }
          } catch (_) { }
          currentMethod = null; currentPath = null;
        }
      }
    }).catch(function (_) { });
  })();
  function pretty(obj) { try { return JSON.stringify(obj, null, 2); } catch (_) { return String(obj); } }
  function appendResult(title, data) {
    var el = document.getElementById('ap-test-result');
    var line = '[' + new Date().toLocaleTimeString() + '] ' + title + ': ' + (typeof data === 'string' ? data : pretty(data));
    el.textContent = (el.textContent ? el.textContent + '\n' : '') + line;
  }
  function send() {
    var method = document.getElementById('ap-test-method').value;
    var path = document.getElementById('ap-test-path').value.trim();
    var bodyText = document.getElementById('ap-test-body').value.trim();
    if (!path) { alert('请输入接口路径'); return; }
    var url = path.startsWith('/') ? path : ('/' + path);
    var opt = { method: method };
    if (method === 'POST') {
      try { opt.body = bodyText ? JSON.stringify(JSON.parse(bodyText)) : '{}'; }
      catch (e) { alert('参数模板需为合法 JSON'); return; }
      opt.headers = { 'Content-Type': 'application/json' };
    }
    fetch(url, opt).then(function (r) { return r.json ? r.json() : r; }).then(function (d) {
      appendResult(method + ' ' + url, d);
      window.UIBus && window.UIBus.publish('api:invoke', { method, url, source: 'api-playground:test' });
    }).catch(function (err) { appendResult('ERROR ' + method + ' ' + url, String(err)); });
  }
  document.getElementById('ap-test-send').addEventListener('click', send);
  document.getElementById('ap-test-load-sample').addEventListener('click', function () {
    var path = document.getElementById('ap-test-path').value.trim();
    if (!path) { alert('请先填写接口路径用于匹配示例'); return; }
    var url = path.startsWith('/') ? path : ('/' + path);
    var sample = samples[url];
    document.getElementById('ap-test-body').value = sample ? pretty(sample) : pretty({ example: '填写 JSON 参数；未知端点暂无示例' });
  });
})();

// 渲染项目状态文档
(function(){
  document.addEventListener('DOMContentLoaded', function(){
    if(document.getElementById('project-status')){
      try{ window.ProjectStatus&&window.ProjectStatus.mount('project-status'); }catch(e){ console.warn('status render failed', e); }
    }
  });
})();

// 与 monitor.html 联动：发布 API 接口清单到 localStorage
(function () {
  function collectEndpoints() {
    var list = [];
    try {
      var sampleKeys = Object.keys(typeof samples !== 'undefined' ? samples : {});
      sampleKeys.forEach(function (p) { list.push({ method: 'GET/POST', path: p }); });
    } catch (_) { }
    try {
      var d = typeof data !== 'undefined' ? data : [];
      d.forEach(function (it) { list.push({ method: 'MIX', path: (it.backend || '').split(',')[0].trim() }); });
    } catch (_) { }
    var seen = new Set();
    list = list.filter(function (x) { var k = x.method + ' ' + x.path; if (seen.has(k)) return false; seen.add(k); return x.path; });
    return list;
  }
  function publish() {
    var payload = { ts: Date.now(), endpoints: collectEndpoints() };
    try { localStorage.setItem('playground:endpoints', JSON.stringify(payload)); } catch (_) { }
    try { window.dispatchEvent(new CustomEvent('playground:endpoints:update', { detail: payload })); } catch (_) { }
  }
  document.addEventListener('DOMContentLoaded', publish);
  setInterval(publish, 15000);
})();
