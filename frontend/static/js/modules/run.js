// stripped module (to be unified later)
void 0;
// Run module: encapsulates UI rendering, events, data fetching
// Ensure CSS via link tag (avoid treating CSS as JS module)
function ensureStyles(){
  const href = '/static/css/modules/run.module.css?v=__ASSET_VERSION__';
  const existed = Array.from(document.styleSheets||[]).some(ss=> ss.href && ss.href.includes('/static/css/modules/run.module.css'));
  if (existed) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = href;
  document.head.appendChild(link);
}

function $(id) { return document.getElementById(id); }

function html(strings, ...vals) {
  const s = strings.reduce((acc, cur, i) => acc + cur + (i < vals.length ? vals[i] : ''), '');
  const tpl = document.createElement('template');
  tpl.innerHTML = s.trim();
  return tpl.content;
}

async function fetchJSON(url, opts = {}) {
  const token = localStorage.getItem('auth_token');
  if (token) {
    opts.headers = opts.headers || {};
    opts.headers['Authorization'] = `Bearer ${token}`;
  }
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

function renderSkeleton() {
  ensureStyles();
  const topbar = $('topbar');
  if (topbar) {
    topbar.innerHTML = '';
    topbar.appendChild(html`
      <div class="topbar">
        <div class="brand">YLAI — 机械风监控大屏</div>
        <div class="controls">
          <button class="btn" id="toggleTheme">切换主题</button>
          <button class="btn" id="fullBtn">全屏</button>
          <span id="global-health-indicator" title="服务健康状态" style="display:inline-flex;align-items:center;gap:6px;padding:2px 8px;border-radius:999px;background:#16222A;color:#e0f7ff;margin-left:8px;">
            <span id="ghi-dot" style="width:10px;height:10px;border-radius:999px;background:#9ca3af;display:inline-block"></span>
            <span id="ghi-text" style="font-size:12px;">未连接</span>
          </span>
        </div>
      </div>
    `);
  }

  const left = $('left-pane');
  if (left) {
    left.innerHTML = '';
    left.appendChild(html`
      <section class="card" id="panel-controls">
        <h3>控制面板</h3>
        <div style="margin-top:8px;display:grid;gap:8px" class="run-form">
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
        <h3>运行结果</h3>
        <pre id="runResult" class="run-result"></pre>
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
    const res = await fetchJSON('/api/crawler/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script: name, params })
    });
    resultEl.textContent = typeof res === 'string' ? res : JSON.stringify(res, null, 2);
    showToastSafe('脚本运行完成', 'success');
  } catch (e) {
    showToastSafe(`运行失败: ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '运行脚本'; }
  }
}

export async function mount(root, options = {}) {
  renderSkeleton();
  await loadScripts();
  const btn = $('runBtn');
  if (btn) btn.onclick = submitRun;
  if (root) root.style.opacity = 1;
}

export default mount;
