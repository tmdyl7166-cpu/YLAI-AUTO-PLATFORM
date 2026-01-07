// stripped page controller
void 0;
(async ()=>{ try { const { mountModule } = await import('../modules/registry.js?v=__ASSET_VERSION__'); const ok = await mountModule('visual_pipeline'); if (ok) return; } catch (_) { /* fallback to local below */ } })();
// Minimal clickable module placeholder guard
(function ensureMinimal(){
  const root = document.getElementById('visual-pipeline-root');
  if (root && !root.children.length) {
    const section = document.createElement('section');
    section.className = 'card';
    const btn = document.createElement('button');
    btn.className = 'btn';
    btn.textContent = '打开 DAG 编辑器';
    btn.onclick = ()=> alert('DAG 占位（后续由模块渲染）');
    section.appendChild(btn);
    root.appendChild(section);
  }
})();
// Visual Pipeline page: DAG editing & WS updates
// Prefer unified module mounting; fallback to local implementation when module missing

// visual_pipeline: single-entry ES module that renders the entire page
// Hidden-then-reveal pattern to avoid flash

// Global-ish state
let dashboard = { role: 'user', features: [] };
let authToken = null;
const BACKEND_ORIGIN = '';
let backendHost = location.host;
const EngineAPI = {
  simple: { run: '/api/pipeline/simple/run', ws: '/api/pipeline/simple/ws/' },
  ws: { run: '/api/pipeline/run', ws: '/ws/pipeline/' }
};
let selectedEngine = 'simple';
let taskState = {}; // { taskId: { nodes: {}, logs: [] } }
let wsConnections = {};
let nodes = []; // {id, script, category, params, condition, x, y, depends_on}
let connections = []; // {from, to}
let selectedNodeId = null;
let shiftFirst = null;
let currentDocId = 'task_1';

// Utilities
function showToast(msg) {
  const div = document.createElement('div');
  div.innerText = msg;
  Object.assign(div.style, {
    position: 'fixed', bottom: '20px', left: '50%', transform: 'translateX(-50%)',
    background: '#333', color: '#fff', padding: '5px 10px', borderRadius: '4px', opacity: 0.92,
    zIndex: 9999
  });
  document.body.appendChild(div);
  setTimeout(() => { try { document.body.removeChild(div); } catch {} }, 1800);
}
function getRunUrl() { return BACKEND_ORIGIN + EngineAPI[selectedEngine].run; }
function getWsUrl(taskId) { return `ws://${backendHost}` + EngineAPI[selectedEngine].ws + taskId; }

async function getAuthHeaders() {
  try {
    const mod = await import('/static/js/auth.js');
    authToken = mod.auth.getToken();
    const h = {};
    if (authToken) h['Authorization'] = `Bearer ${authToken}`;
    return h;
  } catch {
    return {};
  }
}

async function fetchFeatures() {
  try {
    const h = await getAuthHeaders();
    const r = await fetch('/api/dashboard/features', { headers: h });
    const j = await r.json();
    if (j && j.code === 0 && j.data) { dashboard = j.data; }
  } catch {}
}

// Renderers
function renderTopbar() {
  // 仅确保占位容器存在，实际导航由 common/topbar.js 统一渲染
  const top = document.getElementById('topbar') || document.body.appendChild(document.createElement('header'));
  top.id = 'topbar';
}

function renderLayout() {
  const root = document.getElementById('visual-pipeline-root') || document.body.appendChild(document.createElement('main'));
  root.id = 'visual-pipeline-root';
  root.innerHTML = `
    <section style="display:flex;flex-direction:row;height:calc(100vh - 56px);">
      <aside id="sidebar" style="width:300px;background:#0f172a;padding:10px;overflow:auto;border-right:1px solid #1f2937;display:flex;flex-direction:column;color:#e5e7eb;">
        <section id="toolbar" style="margin-bottom:10px;display:flex;gap:8px;align-items:center;">
          <button id="addNodeBtn">➕ 新增节点</button>
          <button id="runAllBtn" title="运行当前 DAG">▶ 运行</button>
        </section>
        <section style="margin-bottom:10px;font-weight:600;">节点模板库</section>
        <section id="templateDynamic"></section>
        <section style="margin-top:18px;">
          <label for="engineSelect" style="font-weight:600;">执行引擎：</label>
          <select id="engineSelect" style="margin-bottom:8px;">
            <option value="simple">Simple</option>
            <option value="ws">WS</option>
          </select>
          <br>
          <label for="maxPipesInput" style="font-weight:600;">最大并发数：</label>
          <input id="maxPipesInput" type="number" min="1" value="2" style="width:72px;">
          <button id="setMaxPipesBtn" style="margin-left:8px;">设置</button>
          <br>
          <label for="globalPolicy" style="font-weight:600;">全局策略：</label>
          <select id="globalPolicy" style="width:96px;">
            <option value="1">等级1</option>
            <option value="2">等级2</option>
            <option value="3">等级3</option>
          </select>
          <button id="applyPolicyBtn" style="margin-left:8px;">应用</button>
        </section>
      </aside>
      <section id="center" style="flex:1;display:flex;flex-direction:column;background:#0b0f14;color:#e5e7eb;">
        <section id="canvas" style="flex:1;position:relative;background:#0b1220;border-bottom:1px solid #1f2937;"></section>
        <section id="logsWrap" style="display:flex;flex-direction:row;gap:12px;margin-top:10px;min-height:200px;">
          <section id="tasksList" style="min-width:200px;"></section>
          <section style="flex:1; display:flex; flex-direction:column;">
            <section style="display:flex; align-items:center; gap:8px;">
              <input id="logFilter" placeholder="按 node_id 过滤日志" />
              <button id="exportBtn">📤 导出 JSON</button>
              <label>📥 导入 JSON <input id="importInput" type="file" accept="application/json" style="font-size:12px;"/></label>
            </section>
            <section id="logs" style="flex:1;overflow:auto;"></section>
          </section>
        </section>
      </section>
      <aside id="docPanel" style="width:380px;background:#0f172a;border-left:1px solid #1f2937;display:flex;flex-direction:column;color:#e5e7eb;">
        <section id="docHeader" style="display:flex;align-items:center;gap:8px;padding:8px 8px;">
          <input id="docIdInput" value="task_1" style="width:140px;" />
          <button id="loadDocBtn">读取文档</button>
          <input id="ai-prompt-input" placeholder="输入任务（中文）" style="flex:1;min-width:180px;margin-left:8px;" />
          <button id="ai-run-btn">运行 AI</button>
        </section>
        <section id="taskDoc" style="flex:1;overflow:auto;padding:8px;">在此显示任务文档（Markdown）</section>
        <section style="padding:8px;border-top:1px solid #1f2937">
          <div style="font-weight:600;margin-bottom:6px">项目任务与部署状态</div>
          <div id="project-status"></div>
          <pre id="ai-result" style="margin-top:8px;white-space:pre-wrap;max-height:180px;overflow:auto"></pre>
        </section>
      </aside>
    </section>
  `;
}

// Backend modules list → template buttons
function loadBackendModules() {
  import('/static/js/modules.js')
    .then(({ apiModules, printVersion }) => {
      apiModules().then(list => {
        list = Array.isArray(list) ? list : [];
        const wrap = document.getElementById('templateDynamic');
        if (!wrap) return;
        wrap.innerHTML = '';
        list.forEach(name => {
          const div = document.createElement('div');
          const btn = document.createElement('button');
          btn.className = 'template-btn';
          btn.dataset.script = name;
          btn.dataset.category = 'spider';
          btn.textContent = name;
          div.appendChild(btn);
          wrap.appendChild(div);
        });
        wrap.querySelectorAll('.template-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            addNode(40, 40, btn.dataset.script, btn.dataset.category, {});
            drawWires();
          });
        });
        printVersion && printVersion();
        window.addEventListener('modules:invoke', (e) => {
          console.debug('[visual-pipeline] invoke', e.detail);
        }, { passive: true });
      });
    })
    .catch(() => { });
}

// Scheduler + policy
async function bindControls() {
  const engineSelect = document.getElementById('engineSelect');
  const maxPipesInput = document.getElementById('maxPipesInput');
  const setMaxPipesBtn = document.getElementById('setMaxPipesBtn');
  const globalPolicySelect = document.getElementById('globalPolicy');
  const applyPolicyBtn = document.getElementById('applyPolicyBtn');

  const params = new URLSearchParams(window.location.search);
  selectedEngine = params.get('engine') || localStorage.getItem('selectedEngine') || 'simple';
  if (engineSelect) engineSelect.value = selectedEngine;
  engineSelect?.addEventListener('change', (e) => {
    selectedEngine = e.target.value;
    localStorage.setItem('selectedEngine', selectedEngine);
    const url = new URL(window.location);
    url.searchParams.set('engine', selectedEngine);
    window.history.replaceState({}, '', url);
    showToast(`当前执行引擎: ${selectedEngine.toUpperCase()}`);
  });

  async function fetchSchedulerConfig() {
    try {
      const h = await getAuthHeaders();
      const res = await fetch(`/api/scheduler/config`, { headers: h });
      const js = await res.json();
      if (maxPipesInput) maxPipesInput.value = js.data?.max_concurrent_pipelines || 2;
    } catch { }
  }
  setMaxPipesBtn?.addEventListener('click', async () => {
    const n = Math.max(1, parseInt(maxPipesInput?.value || '2', 10));
    const h = await getAuthHeaders();
    await fetch(`/api/scheduler/config`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', ...h },
      body: JSON.stringify({ max_concurrent_pipelines: n })
    });
    showToast(`已设置并行管道数为 ${n}`);
    fetchSchedulerConfig();
  });
  fetchSchedulerConfig();

  applyPolicyBtn?.addEventListener('click', async () => {
    const level = parseInt(globalPolicySelect?.value || '1', 10);
    try {
      const h = await getAuthHeaders();
      const res = await fetch(`/api/policy/set`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...h },
        body: JSON.stringify({ level })
      });
      const js = await res.json();
      if (js.code === 0) { showToast(`已应用全局策略等级：${level}`); } else { showToast('策略设置失败'); }
    } catch { showToast('策略设置接口不可用'); }
  });
}

// Docs + AI quick run + project status
function bindDocs() {
  const docInput = document.getElementById('docIdInput');
  const loadDocBtn = document.getElementById('loadDocBtn');
  loadDocBtn?.addEventListener('click', () => {
    currentDocId = (docInput?.value || 'task_1');
    loadTaskDoc(currentDocId);
  });
  loadTaskDoc(currentDocId);

  const aiBtn = document.getElementById('ai-run-btn');
  const aiInput = document.getElementById('ai-prompt-input');
  const aiOut = document.getElementById('ai-result');
  aiBtn?.addEventListener('click', async () => {
    const prompt = (aiInput?.value || '').trim();
    if (!prompt) return;
    aiBtn.disabled = true; aiBtn.textContent = '运行中...';
    try {
      const res = await fetch('/ai/pipeline', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const data = await res.json();
      const result = data.result || data.data || data;
      if (aiOut) aiOut.textContent = typeof result === 'object' ? JSON.stringify(result, null, 2) : String(result);
    } catch (e) {
      if (aiOut) aiOut.textContent = `AI 调用失败: ${String(e)}`;
    } finally {
      aiBtn.disabled = false; aiBtn.textContent = '运行 AI';
    }
  });

  mountProjectStatus();
}

async function loadTaskDoc(docId) {
  try {
    const res = await fetch(`${BACKEND_ORIGIN}/api/docs/${encodeURIComponent(docId)}`);
    const container = document.getElementById('taskDoc');
    if (!container) return;
    if (res.ok) {
      const md = await res.text();
      container.innerHTML = (window.marked ? marked.parse(md) : md);
    } else {
      container.innerText = '文档不存在';
    }
  } catch {
    const container = document.getElementById('taskDoc');
    if (container) container.innerText = '文档获取失败';
  }
}

async function mountProjectStatus() {
  const el = document.getElementById('project-status');
  if (!el) return;
  el.innerHTML = '<div class="loading">加载任务进度...</div>';
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    const md = (data && data.code === 0 && data.data && data.data.markdown) ? data.data.markdown : '暂无状态';
    el.innerHTML = simpleMarkdown(md);
  } catch (e) {
    el.textContent = `加载失败: ${String(e)}`;
  }
}

function simpleMarkdown(md) {
  const esc = s => s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const lines = md.split(/\r?\n/);
  const html = lines.map(l => {
    if (l.startsWith('# ')) return `<h1>${esc(l.slice(2))}</h1>`;
    if (l.startsWith('## ')) return `<h2>${esc(l.slice(3))}</h2>`;
    if (l.startsWith('### ')) return `<h3>${esc(l.slice(4))}</h3>`;
    if (l.startsWith('- ')) return `<li>${esc(l.slice(2))}</li>`;
    if (l.match(/^\d+\. /)) return `<li>${esc(l.replace(/^\d+\. /, ''))}</li>`;
    if (l.trim() === '') return '';
    return `<p>${esc(l)}</p>`;
  }).join('\n');
  return html.replace(/(<li>[^<]*<\/li>\n?)+/g, m => `<ul>${m}</ul>`);
}

// Logs
function appendLog(taskId, msg) {
  taskState[taskId] = taskState[taskId] || { nodes: {}, logs: [] };
  if (!taskState[taskId].logs) taskState[taskId].logs = [];
  taskState[taskId].logs.push(msg);
  if (taskState[taskId].logs.length > 500) taskState[taskId].logs.shift();
  renderLogs(taskId);
}
function renderLogs(taskId) {
  const logsDiv = document.getElementById('logs');
  const logFilter = document.getElementById('logFilter');
  const cur = taskId || Object.keys(taskState)[Object.keys(taskState).length - 1];
  if (!logsDiv) return;
  if (!cur) { logsDiv.innerHTML = ''; return; }
  const kw = (logFilter?.value || '').trim();
  const list = (taskState[cur].logs || []).filter(line => {
    if (!kw) return true;
    try { const obj = JSON.parse(line.replace(/^>/, '')); return (obj.node_id || '').includes(kw); }
    catch { return line.includes(kw); }
  });
  logsDiv.innerHTML = list.map(m => m).join('<br>');
  logsDiv.scrollTop = logsDiv.scrollHeight;
}

// Graph and nodes
let wires = null;
function ensureWires() {
  const canvas = document.getElementById('canvas');
  if (!canvas) return;
  const exist = document.getElementById('wires');
  if (exist) { wires = exist; return; }
  wires = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  wires.setAttribute('id', 'wires');
  canvas.appendChild(wires);
}
function addNode(x = 40, y = 40, script = 'new_node', category = 'spider', params = {}, id = null, condition = '') {
  const canvas = document.getElementById('canvas');
  if (!canvas) return null;
  ensureWires();
  const nodeId = id || ('node-' + Date.now() + Math.floor(Math.random() * 1000));
  const el = document.createElement('div');
  el.className = 'node waiting';
  el.id = nodeId;
  el.style.left = x + 'px';
  el.style.top = y + 'px';
  el.innerHTML = `<div class="title">${script}</div><div class="progress">⏱ 0s</div><div class="badge" style="display:none;">cached</div>`;
  el.dataset.script = script;
  el.dataset.category = category;
  el.dataset.params = JSON.stringify(params || {});
  el.dataset.condition = condition || '';
  canvas.appendChild(el);
  nodes.push({ id: nodeId, script, category, params, condition: condition || '', x, y, depends_on: [] });
  bindNodeInteractions(el);
  return nodeId;
}
function bindNodeInteractions(el) {
  const canvas = document.getElementById('canvas');
  el.addEventListener('click', (e) => {
    e.stopPropagation();
    const id = el.id;
    if (e.shiftKey) {
      if (shiftFirst && shiftFirst !== id) { addConnection(shiftFirst, id); shiftFirst = null; drawWires(); return; }
      shiftFirst = id; return;
    }
    selectedNodeId = id; renderInspector();
  });
  el.addEventListener('dblclick', () => { selectedNodeId = el.id; renderInspector(true); });
  let dragging = false, startX = 0, startY = 0, offX = 0, offY = 0;
  el.addEventListener('mousedown', (e) => {
    dragging = true; startX = e.clientX; startY = e.clientY;
    const r = el.getBoundingClientRect(); offX = startX - r.left; offY = startY - r.top;
  });
  document.addEventListener('mousemove', (e) => {
    if (!dragging) return; if (!canvas) return;
    const nx = e.clientX - offX - canvas.getBoundingClientRect().left;
    const ny = e.clientY - offY - canvas.getBoundingClientRect().top;
    el.style.left = nx + 'px'; el.style.top = ny + 'px';
    const nd = nodes.find(n => n.id === el.id); if (nd) { nd.x = nx; nd.y = ny; }
    drawWires();
  });
  document.addEventListener('mouseup', () => { dragging = false; });
}
function addConnection(fromId, toId) {
  if (fromId === toId) return;
  if (connections.find(c => c.from === fromId && c.to === toId)) return;
  connections.push({ from: fromId, to: toId });
  const toNode = nodes.find(n => n.id === toId);
  if (toNode) { toNode.depends_on.push(fromId); }
}
function drawWires() {
  ensureWires(); if (!wires) return;
  wires.innerHTML = '';
  connections.forEach(c => {
    const a = document.getElementById(c.from);
    const b = document.getElementById(c.to);
    if (!a || !b) return;
    const ax = a.offsetLeft + a.offsetWidth / 2;
    const ay = a.offsetTop + a.offsetHeight / 2;
    const bx = b.offsetLeft + b.offsetWidth / 2;
    const by = b.offsetTop + b.offsetHeight / 2;
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const dx = Math.abs(bx - ax) * 0.4;
    const d = `M ${ax} ${ay} C ${ax + dx} ${ay}, ${bx - dx} ${by}, ${bx} ${by}`;
    path.setAttribute('d', d);
    path.setAttribute('stroke', '#64748b');
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke-width', '2');
    wires.appendChild(path);
  });
}

// Inspector
function mountInspector() {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;
  const inspectorWrap = document.createElement('div');
  inspectorWrap.id = 'inspector';
  inspectorWrap.innerHTML = `
    <h4>节点参数</h4>
    <div>选中节点：<span id="inspId">-</span></div>
    <div>脚本：<input id="inspScript" style="width:100%" /></div>
    <div>分类：
      <select id="inspCategory">
        <option value="spider">spider</option>
        <option value="ai">ai</option>
        <option value="process">process</option>
        <option value="data">data</option>
      </select>
    </div>
    <div>条件（可选）：<input id="inspCondition" placeholder="如 up.dep1 != null" style="width:100%" /></div>
    <div>参数(JSON)：<textarea id="inspParams" placeholder='{"url":"https://example.com"}'></textarea></div>
    <div style="margin-top:6px; display:flex; gap:8px;">
      <button id="inspSave">保存</button>
      <button id="inspDelete">删除节点</button>
    </div>
  `;
  sidebar.appendChild(inspectorWrap);

  document.getElementById('inspSave')?.addEventListener('click', () => {
    const nd = nodes.find(n => n.id === selectedNodeId); if (!nd) return;
    const si = document.getElementById('inspScript');
    const sc = document.getElementById('inspCategory');
    const scd = document.getElementById('inspCondition');
    const sp = document.getElementById('inspParams');
    nd.script = (si?.value || '').trim() || nd.script;
    nd.category = sc?.value || nd.category;
    nd.condition = (scd?.value || '').trim();
    try { nd.params = JSON.parse(sp?.value || '{}'); }
    catch (e) { showToast('参数JSON解析失败'); return; }
    const el = document.getElementById(nd.id);
    if (el) {
      el.querySelector('.title').textContent = nd.script;
      el.dataset.params = JSON.stringify(nd.params || {});
      el.dataset.category = nd.category;
      el.dataset.condition = nd.condition || '';
    }
    showToast('已保存');
  });
  document.getElementById('inspDelete')?.addEventListener('click', () => {
    if (!selectedNodeId) return;
    connections = connections.filter(c => c.from !== selectedNodeId && c.to !== selectedNodeId);
    const i = nodes.findIndex(n => n.id === selectedNodeId);
    if (i >= 0) nodes.splice(i, 1);
    const el = document.getElementById(selectedNodeId); if (el) el.remove();
    selectedNodeId = null; drawWires(); renderInspector();
  });
}
function renderInspector(focus = false) {
  const idSpan = document.getElementById('inspId');
  const si = document.getElementById('inspScript');
  const sc = document.getElementById('inspCategory');
  const scd = document.getElementById('inspCondition');
  const sp = document.getElementById('inspParams');
  if (!selectedNodeId) { if (idSpan) idSpan.textContent = '-'; if (si) si.value = ''; if (sp) sp.value = ''; return; }
  const nd = nodes.find(n => n.id === selectedNodeId); if (!nd) return;
  if (idSpan) idSpan.textContent = selectedNodeId;
  if (si) si.value = nd.script;
  if (sc) sc.value = nd.category || 'spider';
  if (scd) scd.value = nd.condition || '';
  if (sp) sp.value = JSON.stringify(nd.params || {}, null, 2);
  if (focus && sp) sp.focus();
}

// Export/Import
function bindExportImport() {
  document.getElementById('exportBtn')?.addEventListener('click', () => {
    const data = { nodes: nodes.map(n => ({ id: n.id, script: n.script, category: n.category, params: n.params, condition: n.condition || '', x: n.x || 0, y: n.y || 0, depends_on: [...n.depends_on] })) };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'dag.json'; a.click();
    URL.revokeObjectURL(url);
  });
  document.getElementById('importInput')?.addEventListener('change', async (e) => {
    const file = e.target.files && e.target.files[0]; if (!file) return;
    const text = await file.text();
    try {
      const data = JSON.parse(text);
      nodes = []; connections = []; selectedNodeId = null;
      document.getElementById('canvas')?.querySelectorAll('.node').forEach(n => n.remove());
      document.getElementById('wires')?.remove(); ensureWires();
      (data.nodes || []).forEach(n => { addNode(n.x || 40, n.y || 40, n.script, n.category || 'spider', n.params || {}, n.id, n.condition || ''); });
      (data.nodes || []).forEach(n => { (n.depends_on || []).forEach(dep => addConnection(dep, n.id)); });
      drawWires(); showToast('导入完成');
    } catch { showToast('导入失败：JSON 解析错误'); }
  });
}

// Run + WS
function buildDagPayload() { return { nodes: nodes.map(n => ({ id: n.id, script: n.script, category: n.category, params: n.params, condition: n.condition || undefined, depends_on: [...n.depends_on] })) }; }
async function runAll() {
  const runUrl = getRunUrl(); const h = await getAuthHeaders();
  fetch(runUrl, { method: 'POST', headers: { 'Content-Type': 'application/json', ...h }, body: JSON.stringify(buildDagPayload()) })
    .then(res => res.json())
    .then(data => { const taskId = data.task_id; taskState[taskId] = { nodes: {}, logs: [], progress: 0 }; connectWS(taskId); appendLog(taskId, `任务 ${taskId} 已启动`); loadTaskDoc(currentDocId); });
}
function connectWS(taskId) {
  if (wsConnections[taskId]) wsConnections[taskId].close();
  let retryDelay = 1000;
  const _connect = () => {
    const tok = authToken; const url = tok ? getWsUrl(taskId) + `?token=${encodeURIComponent(tok)}` : getWsUrl(taskId);
    const ws = new WebSocket(url); wsConnections[taskId] = ws;
    ws.onopen = () => { appendLog(taskId, 'WS已连接'); try { ws.send(JSON.stringify({ type: 'resume', taskId })); } catch {} retryDelay = 1000; };
    ws.onmessage = (evt) => {
      const data = JSON.parse(evt.data);
      const nodeId = data.node_id || data.nodeId; const status = data.status || (data.type === 'node_update' ? (data.status || '') : ''); const elapsed = data.elapsed || 0;
      if (nodeId && (status || data.type === 'node_update')) { updateNodeState(taskId, nodeId, status, elapsed, { cached: data.cached }); const docNodeEl = document.getElementById(`doc-${nodeId}`); if (docNodeEl) { docNodeEl.innerText = `${status || 'update'} (${elapsed}s)`; } }
      appendLog(taskId, JSON.stringify(data));
    };
    ws.onclose = () => { appendLog(taskId, 'WS断开，尝试重连...'); setTimeout(() => { retryDelay = Math.min(retryDelay * 2, 30000); _connect(); }, retryDelay); };
    ws.onerror = (err) => { console.error('WS错误', err); };
  };
  _connect();
}
function updateNodeState(taskId, nodeId, status, elapsed, extra) {
  const nodeEl = document.getElementById(nodeId); if (!nodeEl) return;
  nodeEl.className = 'node ' + status;
  const prog = nodeEl.querySelector('.progress'); if (prog) prog.textContent = `⏱ ${elapsed || 0}s`;
  const badge = nodeEl.querySelector('.badge'); if (badge) badge.style.display = (extra && extra.cached) ? 'block' : 'none';
  taskState[taskId].nodes[nodeId] = status; updateProgress(taskId);
}
function updateProgress(taskId) {
  const ns = Object.values(taskState[taskId].nodes);
  const completed = ns.filter(s => s === 'success' || s === 'failed').length;
  const total = ns.length; const percent = total ? Math.round(completed / total * 100) : 0;
  let panel = document.getElementById('task-' + taskId);
  if (!panel) {
    const item = document.createElement('div'); item.className = 'taskItem'; item.id = 'task-' + taskId;
    item.innerHTML = `<div class="taskTitle">任务 ${taskId}</div><div class="progressOuter"><div class="progressInner" id="progress-${taskId}"></div></div>`;
    document.getElementById('tasksList')?.appendChild(item);
  }
  const bar = document.getElementById(`progress-${taskId}`); if (bar) bar.style.width = percent + '%';
}

// Feature/role gating
function applyGating() {
  try {
    const runBtn = document.getElementById('runAllBtn');
    if (runBtn) {
      const allowed = dashboard.features.includes('recognize') || dashboard.features.includes('collect') || dashboard.features.includes('enum');
      runBtn.style.display = allowed ? '' : 'none';
    }
    const role = String(dashboard.role || 'user');
    const adminOnly = ['applyPolicyBtn'];
    const superOnly = [];
    adminOnly.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = (role === 'admin' || role === 'superadmin') ? '' : 'none'; });
    superOnly.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = (role === 'superadmin') ? '' : 'none'; });
  } catch { }
}

// Init
function bindCanvasAndActions() {
  const canvas = document.getElementById('canvas');
  canvas?.addEventListener('click', () => { selectedNodeId = null; renderInspector(); });
  document.getElementById('addNodeBtn')?.addEventListener('click', () => { addNode(40, 40, 'custom', 'spider', {}); drawWires(); });
  document.getElementById('runAllBtn')?.addEventListener('click', runAll);
}

async function init() {
  renderTopbar();
  renderLayout();
  ensureWires();
  bindCanvasAndActions();
  mountInspector();
  bindExportImport();
  await bindControls();
  bindDocs();
  loadBackendModules();
  await fetchFeatures();
  applyGating();

  // Reveal UI
  const root = document.getElementById('visual-pipeline-root');
  if (root) root.style.opacity = '1';
}

document.addEventListener('DOMContentLoaded', init);
