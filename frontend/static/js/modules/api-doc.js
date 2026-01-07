// API Documentation module: interactive API documentation
function ensureStyles(){
  const href = '/static/css/modules/api-doc.module.css?v=__ASSET_VERSION__';
  const existed = Array.from(document.styleSheets||[]).some(ss=> ss.href && ss.href.includes('/static/css/modules/api-doc.module.css'));
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
    console[type === 'error' ? 'log']('[toast]', msg);
  }
}

let apiData = null;

function renderApiDocDashboard() {
  ensureStyles();
  const root = $('app-root');
  if (!root) return;

  root.innerHTML = '';
  root.appendChild(html`
    <div class="api-doc-dashboard">
      <header class="api-doc-header">
        <h1>API 文档</h1>
        <div class="api-doc-controls">
          <input type="text" id="searchInput" placeholder="搜索API..." class="search-input">
          <select id="categoryFilter" class="filter-select">
            <option value="">所有分类</option>
            <option value="auth">认证</option>
            <option value="scripts">脚本</option>
            <option value="monitor">监控</option>
            <option value="system">系统</option>
          </select>
          <button id="refreshBtn" class="btn btn-primary">刷新</button>
        </div>
      </header>

      <div class="api-content">
        <nav class="api-nav">
          <div id="apiList" class="api-list">
            <div class="loading">加载API列表中...</div>
          </div>
        </nav>

        <main class="api-main">
          <div id="apiDetail" class="api-detail">
            <div class="welcome-message">
              <h2>欢迎使用API文档</h2>
              <p>选择左侧的API端点查看详细文档</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  `);

  // Bind events
  const searchInput = $('searchInput');
  const categoryFilter = $('categoryFilter');
  const refreshBtn = $('refreshBtn');

  if (searchInput) {
    searchInput.addEventListener('input', () => filterApis());
  }

  if (categoryFilter) {
    categoryFilter.addEventListener('change', () => filterApis());
  }

  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => loadApiDocs());
  }
}

async function loadApiDocs() {
  try {
    // Load API documentation from backend
    const docs = await fetchJSON('/api/docs');
    apiData = docs;
    renderApiList(docs.endpoints || []);
  } catch (error) {
    showToastSafe('加载API文档失败: ' + error.message, 'error');
    renderFallbackApiList();
  }
}

function renderApiList(endpoints) {
  const apiList = $('apiList');
  if (!apiList) return;

  if (!endpoints || endpoints.length === 0) {
    apiList.innerHTML = '<div class="no-apis">暂无API文档</div>';
    return;
  }

  apiList.innerHTML = '';
  endpoints.forEach(endpoint => {
    const item = document.createElement('div');
    item.className = 'api-item';
    item.dataset.category = endpoint.category || 'system';
    item.innerHTML = `
      <div class="api-method ${endpoint.method.toLowerCase()}">${endpoint.method}</div>
      <div class="api-path">${endpoint.path}</div>
      <div class="api-summary">${endpoint.summary || '无描述'}</div>
    `;
    item.addEventListener('click', () => showApiDetail(endpoint));
    apiList.appendChild(item);
  });
}

function renderFallbackApiList() {
  const apiList = $('apiList');
  if (!apiList) return;

  const fallbackEndpoints = [
    { method: 'GET', path: '/health', summary: '健康检查', category: 'system' },
    { method: 'POST', path: '/api/auth/login', summary: '用户登录', category: 'auth' },
    { method: 'GET', path: '/api/scripts', summary: '获取脚本列表', category: 'scripts' },
    { method: 'POST', path: '/api/crawler/start', summary: '启动爬虫任务', category: 'scripts' },
    { method: 'GET', path: '/api/monitor/metrics', summary: '获取监控指标', category: 'monitor' },
    { method: 'GET', path: '/api/docs', summary: '获取API文档', category: 'system' }
  ];

  renderApiList(fallbackEndpoints);
}

function showApiDetail(endpoint) {
  const apiDetail = $('apiDetail');
  if (!apiDetail) return;

  apiDetail.innerHTML = `
    <div class="api-detail-header">
      <span class="api-method ${endpoint.method.toLowerCase()}">${endpoint.method}</span>
      <h2>${endpoint.path}</h2>
      <p class="api-summary">${endpoint.summary || '无描述'}</p>
    </div>

    <div class="api-detail-content">
      ${endpoint.description ? `<div class="api-description"><h3>描述</h3><p>${endpoint.description}</p></div>` : ''}

      ${endpoint.parameters && endpoint.parameters.length > 0 ? `
        <div class="api-parameters">
          <h3>参数</h3>
          <table class="params-table">
            <thead>
              <tr>
                <th>参数名</th>
                <th>类型</th>
                <th>必需</th>
                <th>描述</th>
              </tr>
            </thead>
            <tbody>
              ${endpoint.parameters.map(param => `
                <tr>
                  <td>${param.name}</td>
                  <td>${param.type || 'string'}</td>
                  <td>${param.required ? '是' : '否'}</td>
                  <td>${param.description || ''}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      ` : ''}

      ${endpoint.responses ? `
        <div class="api-responses">
          <h3>响应</h3>
          <div class="response-examples">
            ${Object.entries(endpoint.responses).map(([code, response]) => `
              <div class="response-item">
                <div class="response-code ${code.startsWith('2') ? 'success' : code.startsWith('4') ? 'error' : 'info'}">${code}</div>
                <div class="response-desc">${response.description || ''}</div>
                ${response.example ? `<pre class="response-example">${JSON.stringify(response.example, null, 2)}</pre>` : ''}
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}

      <div class="api-try-it">
        <h3>测试接口</h3>
        <button id="tryApiBtn" class="btn btn-secondary">发送请求</button>
        <div id="tryResult" class="try-result" style="display: none;"></div>
      </div>
    </div>
  `;

  // Bind try it button
  const tryApiBtn = $('tryApiBtn');
  if (tryApiBtn) {
    tryApiBtn.addEventListener('click', () => tryApiCall(endpoint));
  }
}

async function tryApiCall(endpoint) {
  const tryResult = $('tryResult');
  if (!tryResult) return;

  tryResult.style.display = 'block';
  tryResult.innerHTML = '<div class="loading">发送请求中...</div>';

  try {
    const response = await fetchJSON(endpoint.path, {
      method: endpoint.method,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    tryResult.innerHTML = `
      <div class="response-success">
        <h4>响应状态: 200 OK</h4>
        <pre>${JSON.stringify(response, null, 2)}</pre>
      </div>
    `;
  } catch (error) {
    tryResult.innerHTML = `
      <div class="response-error">
        <h4>请求失败: ${error.message}</h4>
      </div>
    `;
  }
}

function filterApis() {
  const searchInput = $('searchInput');
  const categoryFilter = $('categoryFilter');
  const apiItems = document.querySelectorAll('.api-item');

  const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
  const category = categoryFilter ? categoryFilter.value : '';

  apiItems.forEach(item => {
    const path = item.querySelector('.api-path').textContent.toLowerCase();
    const summary = item.querySelector('.api-summary').textContent.toLowerCase();
    const itemCategory = item.dataset.category;

    const matchesSearch = path.includes(searchTerm) || summary.includes(searchTerm);
    const matchesCategory = !category || itemCategory === category;

    item.style.display = matchesSearch && matchesCategory ? 'block' : 'none';
  });
}

export async function mount(root, options = {}) {
  console.log('API Doc module mounting...');
  renderApiDocDashboard();
  await loadApiDocs();
  return { root, options };
}

export default mount;
