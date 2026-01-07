// Security module: 系统安全策略管理
function ensureStyles(){
  const href = '/static/css/modules/security.module.css?v=__ASSET_VERSION__';
  const existed = Array.from(document.styleSheets||[]).some(ss=> ss.href && ss.href.includes('/static/css/modules/security.module.css'));
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

function renderSecurityDashboard() {
  ensureStyles();
  const root = $('app-root');
  if (!root) return;

  root.innerHTML = '';
  root.appendChild(html`
    <div class="security-dashboard">
      <header class="security-header">
        <h1>安全策略管理</h1>
        <div class="security-controls">
          <button id="refreshBtn" class="btn btn-primary">刷新状态</button>
          <button id="securityScanBtn" class="btn btn-secondary">安全扫描</button>
        </div>
      </header>

      <div class="security-content">
        <div class="security-tabs">
          <button class="tab-btn active" data-tab="overview">安全概览</button>
          <button class="tab-btn" data-tab="rate-limit">限流配置</button>
          <button class="tab-btn" data-tab="keys">API密钥</button>
          <button class="tab-btn" data-tab="threats">威胁检测</button>
        </div>

        <div class="tab-content">
          <div id="overviewTab" class="tab-pane active">
            <div class="security-overview">
              <div class="metric-grid">
                <div class="metric-card">
                  <h3>WAF状态</h3>
                  <div id="wafStatus" class="status-indicator">
                    <span class="status loading">检查中...</span>
                  </div>
                </div>

                <div class="metric-card">
                  <h3>限流统计</h3>
                  <div id="rateLimitStats" class="stats-display">
                    <div class="stat-item">
                      <span class="label">今日请求:</span>
                      <span id="todayRequests" class="value">--</span>
                    </div>
                    <div class="stat-item">
                      <span class="label">被限流:</span>
                      <span id="blockedRequests" class="value">--</span>
                    </div>
                  </div>
                </div>

                <div class="metric-card">
                  <h3>威胁检测</h3>
                  <div id="threatStats" class="stats-display">
                    <div class="stat-item">
                      <span class="label">检测到威胁:</span>
                      <span id="threatCount" class="value">--</span>
                    </div>
                    <div class="stat-item">
                      <span class="label">拦截成功:</span>
                      <span id="blockedThreats" class="value">--</span>
                    </div>
                  </div>
                </div>

                <div class="metric-card">
                  <h3>API密钥</h3>
                  <div id="keyStats" class="stats-display">
                    <div class="stat-item">
                      <span class="label">活跃密钥:</span>
                      <span id="activeKeys" class="value">--</span>
                    </div>
                    <div class="stat-item">
                      <span class="label">过期密钥:</span>
                      <span id="expiredKeys" class="value">--</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div id="rateLimitTab" class="tab-pane">
            <div class="rate-limit-config">
              <h2>限流配置</h2>
              <div class="config-section">
                <h3>全局限流</h3>
                <div class="config-item">
                  <label>每分钟请求限制:</label>
                  <input type="number" id="globalRateLimit" value="1000" min="1">
                  <button class="btn btn-primary" onclick="updateRateLimit('global')">更新</button>
                </div>
              </div>

              <div class="config-section">
                <h3>IP限流</h3>
                <div class="config-item">
                  <label>IP每分钟限制:</label>
                  <input type="number" id="ipRateLimit" value="100" min="1">
                  <button class="btn btn-primary" onclick="updateRateLimit('ip')">更新</button>
                </div>
              </div>

              <div class="config-section">
                <h3>用户限流</h3>
                <div class="config-item">
                  <label>用户每分钟限制:</label>
                  <input type="number" id="userRateLimit" value="500" min="1">
                  <button class="btn btn-primary" onclick="updateRateLimit('user')">更新</button>
                </div>
              </div>
            </div>
          </div>

          <div id="keysTab" class="tab-pane">
            <div class="api-keys-management">
              <div class="tab-header">
                <h2>API密钥管理</h2>
                <button id="createKeyBtn" class="btn btn-primary">创建密钥</button>
              </div>
              <div id="keysList" class="keys-list">
                <div class="loading">加载密钥列表中...</div>
              </div>
            </div>
          </div>

          <div id="threatsTab" class="tab-pane">
            <div class="threat-detection">
              <h2>威胁检测日志</h2>
              <div id="threatsList" class="threats-list">
                <div class="loading">加载威胁日志中...</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `);

  // Bind events
  const refreshBtn = $('refreshBtn');
  const securityScanBtn = $('securityScanBtn');
  const tabBtns = document.querySelectorAll('.tab-btn');
  const createKeyBtn = $('createKeyBtn');

  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => loadSecurityData());
  }

  if (securityScanBtn) {
    securityScanBtn.addEventListener('click', () => runSecurityScan());
  }

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  if (createKeyBtn) {
    createKeyBtn.addEventListener('click', () => showCreateKeyDialog());
  }
}

function switchTab(tabName) {
  // Update tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });

  // Update tab content
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `${tabName}Tab`);
  });

  // Load data for the selected tab
  loadTabData(tabName);
}

async function loadSecurityData() {
  try {
    // Load WAF status
    const wafStatus = await fetchJSON('/api/security/waf/status');
    updateWafStatus(wafStatus);

    // Load rate limit stats
    const rateStats = await fetchJSON('/api/security/rate-limit/stats');
    updateRateLimitStats(rateStats);

    // Load threat stats
    const threatStats = await fetchJSON('/api/security/threats/stats');
    updateThreatStats(threatStats);

    // Load key stats
    const keyStats = await fetchJSON('/api/keys/stats');
    updateKeyStats(keyStats);

  } catch (error) {
    showToastSafe('加载安全数据失败: ' + error.message, 'error');
  }
}

function updateWafStatus(status) {
  const wafStatusEl = $('wafStatus');
  if (!wafStatusEl) return;

  const isActive = status.enabled;
  wafStatusEl.innerHTML = `<span class="status ${isActive ? 'active' : 'inactive'}">${isActive ? '🛡️ 启用' : '⚠️ 禁用'}</span>`;
}

function updateRateLimitStats(stats) {
  const todayRequests = $('todayRequests');
  const blockedRequests = $('blockedRequests');

  if (todayRequests) todayRequests.textContent = stats.today_requests || 0;
  if (blockedRequests) blockedRequests.textContent = stats.blocked_requests || 0;
}

function updateThreatStats(stats) {
  const threatCount = $('threatCount');
  const blockedThreats = $('blockedThreats');

  if (threatCount) threatCount.textContent = stats.total_threats || 0;
  if (blockedThreats) blockedThreats.textContent = stats.blocked_threats || 0;
}

function updateKeyStats(stats) {
  const activeKeys = $('activeKeys');
  const expiredKeys = $('expiredKeys');

  if (activeKeys) activeKeys.textContent = stats.active_keys || 0;
  if (expiredKeys) expiredKeys.textContent = stats.expired_keys || 0;
}

async function loadTabData(tabName) {
  switch (tabName) {
    case 'keys':
      await loadKeysList();
      break;
    case 'threats':
      await loadThreatsList();
      break;
  }
}

async function loadKeysList() {
  const keysList = $('keysList');
  if (!keysList) return;

  try {
    const keys = await fetchJSON('/api/keys/list');
    renderKeysList(keys.data || []);
  } catch (error) {
    keysList.innerHTML = `<div class="error">加载密钥列表失败: ${error.message}</div>`;
  }
}

function renderKeysList(keys) {
  const keysList = $('keysList');
  if (!keysList) return;

  if (!keys || keys.length === 0) {
    keysList.innerHTML = '<div class="no-data">暂无API密钥</div>';
    return;
  }

  keysList.innerHTML = '';
  keys.forEach(key => {
    const item = document.createElement('div');
    item.className = 'key-item';
    item.innerHTML = `
      <div class="key-info">
        <div class="key-name">${key.name}</div>
        <div class="key-id">${key.id}</div>
        <div class="key-created">创建时间: ${new Date(key.created_at).toLocaleString()}</div>
        <div class="key-status ${key.active ? 'active' : 'inactive'}">${key.active ? '活跃' : '已撤销'}</div>
      </div>
      <div class="key-actions">
        ${key.active ? `<button class="btn btn-danger btn-sm" onclick="revokeKey('${key.id}')">撤销</button>` : ''}
      </div>
    `;
    keysList.appendChild(item);
  });
}

async function loadThreatsList() {
  const threatsList = $('threatsList');
  if (!threatsList) return;

  try {
    const threats = await fetchJSON('/api/security/threats');
    renderThreatsList(threats.data || []);
  } catch (error) {
    threatsList.innerHTML = `<div class="error">加载威胁日志失败: ${error.message}</div>`;
  }
}

function renderThreatsList(threats) {
  const threatsList = $('threatsList');
  if (!threatsList) return;

  if (!threats || threats.length === 0) {
    threatsList.innerHTML = '<div class="no-data">暂无威胁检测记录</div>';
    return;
  }

  threatsList.innerHTML = '';
  threats.forEach(threat => {
    const item = document.createElement('div');
    item.className = `threat-item ${threat.severity}`;
    item.innerHTML = `
      <div class="threat-info">
        <div class="threat-type">${threat.type}</div>
        <div class="threat-ip">IP: ${threat.ip}</div>
        <div class="threat-time">${new Date(threat.timestamp).toLocaleString()}</div>
        <div class="threat-severity">严重程度: ${threat.severity}</div>
      </div>
      <div class="threat-details">
        ${threat.details || '无详细信息'}
      </div>
    `;
    threatsList.appendChild(item);
  });
}

async function runSecurityScan() {
  try {
    showToastSafe('开始安全扫描...', 'info');
    const result = await fetchJSON('/api/security/scan', {
      method: 'POST'
    });
    showToastSafe('安全扫描完成', 'success');
    await loadSecurityData(); // Refresh data
  } catch (error) {
    showToastSafe('安全扫描失败: ' + error.message, 'error');
  }
}

function showCreateKeyDialog() {
  const dialog = document.createElement('div');
  dialog.className = 'modal-dialog';
  dialog.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h3>创建API密钥</h3>
        <button class="modal-close" onclick="this.closest('.modal-dialog').remove()">×</button>
      </div>
      <div class="modal-body">
        <form id="createKeyForm">
          <div class="form-group">
            <label>密钥名称:</label>
            <input type="text" name="name" required placeholder="输入密钥名称">
          </div>
          <div class="form-group">
            <label>权限范围:</label>
            <select name="scope" multiple>
              <option value="read">读取</option>
              <option value="write">写入</option>
              <option value="admin">管理</option>
            </select>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="this.closest('.modal-dialog').remove()">取消</button>
        <button class="btn btn-primary" onclick="submitCreateKey()">创建</button>
      </div>
    </div>
  `;
  document.body.appendChild(dialog);
}

export async function mount(root, options = {}) {
  console.log('Security module mounting...');
  renderSecurityDashboard();
  await loadSecurityData();
  return { root, options };
}

export default mount;

// Keep the registry part for backward compatibility
export const securityModule = {
  id: 'module.security',
  title: '安全策略',
  node: 'node.security',
  routes: {
    rateLimit: { method: 'POST', path: '/api/security/rate-limit' },
    twoFA: { method: 'POST', path: '/api/security/2fa' },
    wafStatus: { method: 'GET', path: '/api/security/waf/status' },
    uploadScan: { method: 'POST', path: '/api/upload/scan' },
    keyCreate: { method: 'POST', path: '/api/keys/create' },
    keyRevoke: { method: 'POST', path: '/api/keys/revoke' },
    keyList: { method: 'GET', path: '/api/keys/list' },
    ipThrottle: { method: 'POST', path: '/api/security/ip-throttle' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
