// 自动每30秒热重载刷新页面
setInterval(() => {
  if (document.visibilityState === 'visible') {
    window.location.reload();
  }
}, 30000);
// Index module: main dashboard with function cards
function ensureStyles(){
  const href = '/static/css/modules/index.module.css?v=__ASSET_VERSION__';
  const existed = Array.from(document.styleSheets||[]).some(ss=> ss.href && ss.href.includes('/static/css/modules/index.module.css'));
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
  let res;
  try {
    res = await fetch(url, opts);
  } catch (e) {
    showToastSafe('网络请求失败: ' + e.message, 'error');
    throw e;
  }
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  if (res.status === 401) {
    showToastSafe('未授权或登录已过期，请重新登录', 'error');
    window.location.href = '/pages/login.html';
    throw new Error('未授权');
  }
  if (!res.ok) {
    showToastSafe('请求失败: ' + (typeof data === 'string' ? data : JSON.stringify(data)), 'error');
    throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
  }
  return data;
}

function showToastSafe(msg, type = 'info') {
  if (window.showToast) {
    window.showToast({ message: msg, type });
  } else {
    console[type === 'error' ? 'error' : 'log']('[toast]', msg);
  }
}

let functions = [];

async function loadFunctions() {
  try {
    // 优先从统一接口映射表加载（如有），否则 fallback 到 functions.json
    let data;
    try {
      const resp = await fetch('/docs/统一接口映射表.md');
      if (resp.ok) {
        const text = await resp.text();
        // 简单提取 json 块（如有）
        const match = text.match(/```json([\s\S]*?)```/);
        if (match) {
          data = JSON.parse(match[1]);
        }
      }
    } catch {}
    if (!data) {
      data = await fetchJSON('/static/data/functions.json');
    }
    functions = data;
  } catch (e) {
    showToastSafe('功能列表加载失败: ' + e.message, 'error');
    functions = [];
  }
}

function renderFunctionCard(func) {
  const statusIcon = func.status === 'available' ? '🟢' : '🟡';
  const statusText = func.status === 'available' ? '可用' : '脚本模式';

  return html`
    <div class="function-card" data-id="${func.id}">
      <div class="card-header">
        <h3>${func.name}</h3>
        <span class="status">${statusIcon} ${statusText}</span>
      </div>
      <p class="description">${func.desc}</p>
      <div class="card-actions">
        <button class="btn btn-primary run-btn" data-api="${func.api || ''}">启动任务</button>
        <button class="btn btn-secondary view-btn">查看说明</button>
      </div>
    </div>
  `;
}

async function handleRunTask(event) {
  const btn = event.target;
  const card = btn.closest('.function-card');
  const funcId = card.dataset.id;
  const api = btn.dataset.api;

  // 日志记录
  try {
    const logs = JSON.parse(localStorage.getItem('op_logs') || '[]');
    logs.push({
      type: 'run-task',
      funcId,
      time: new Date().toISOString(),
      user: localStorage.getItem('user_role') || 'guest'
    });
    localStorage.setItem('op_logs', JSON.stringify(logs));
  } catch (e) { console.warn('日志记录失败', e); }

  if (!api) {
    showToastSafe('此功能仅支持脚本模式', 'warning');
    return;
  }

  try {
    let payload = {};
    if (funcId === 'demo_run') {
      payload = { message: 'Hello from frontend!' };
    } else if (funcId === 'phone_reverse') {
      const phone = prompt('请输入手机号码:');
      if (!phone) return;
      payload = { phone };
    } else if (funcId === 'ai_task') {
      const prompt = prompt('请输入AI任务描述:');
      if (!prompt) return;
      payload = { prompt };
    }

    const response = await fetchJSON(api, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    showToastSafe('任务启动成功', 'success');
    console.log('Task result:', response);

  } catch (error) {
    showToastSafe('任务启动失败: ' + error.message, 'error');
  }
}

function handleViewDoc(event) {
  const card = event.target.closest('.function-card');
  const funcId = card.dataset.id;
  // 日志记录
  try {
    const logs = JSON.parse(localStorage.getItem('op_logs') || '[]');
    logs.push({
      type: 'view-doc',
      funcId,
      time: new Date().toISOString(),
      user: localStorage.getItem('user_role') || 'guest'
    });
    localStorage.setItem('op_logs', JSON.stringify(logs));
  } catch (e) { console.warn('日志记录失败', e); }
  window.open(`/pages/api-doc.html#${funcId}`, '_blank');
}


async function renderDashboard() {
  ensureStyles();
  const root = $('app-root');
  if (!root) return;

  await loadFunctions();

  root.innerHTML = '';
  root.appendChild(html`
    <div class="dashboard">
      <header class="dashboard-header">
        <h1>YLAI 自动化平台</h1>
        <div class="user-info">
          <span id="user-display">未登录</span>
          <button id="logout-btn" class="btn btn-secondary">登出</button>
        </div>
      </header>

      <div class="functions-grid">
        ${functions.map(renderFunctionCard)}
      </div>

      <div class="quick-actions">
        <a href="/pages/monitor.html" class="btn btn-secondary">系统监控</a>
        <a href="/pages/visual_pipeline.html" class="btn btn-secondary">流程编排</a>
        <a href="/pages/api-doc.html" class="btn btn-secondary">API文档</a>
      </div>
    </div>
  `);

  // Bind events
  root.addEventListener('click', (e) => {
    if (e.target.classList.contains('run-btn')) {
      handleRunTask(e);
    } else if (e.target.classList.contains('view-btn')) {
      handleViewDoc(e);
    } else if (e.target.id === 'logout-btn') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_role');
      window.location.href = '/pages/login.html';
    }
  });

  // Update user info
  const token = localStorage.getItem('auth_token');
  const role = localStorage.getItem('user_role');
  const userDisplay = $('user-display');
  if (userDisplay) {
    userDisplay.textContent = token ? `用户 (${role})` : '未登录';
  }
}


export async function mount(root, options = {}) {
  console.log('Index module mounting...');
  await renderDashboard();
  return { root, options };
}

export default mount;
