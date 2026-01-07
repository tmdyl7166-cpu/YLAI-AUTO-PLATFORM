// System module: 系统设置和管理
function ensureStyles(){
  const href = '/static/css/modules/system.module.css?v=__ASSET_VERSION__';
  const existed = Array.from(document.styleSheets||[]).some(ss=> ss.href && ss.href.includes('/static/css/modules/system.module.css'));
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

let currentSettings = {};

function renderSystemDashboard() {
  ensureStyles();
  const root = $('app-root');
  if (!root) return;

  root.innerHTML = '';
  root.appendChild(html`
    <div class="system-dashboard">
      <header class="system-header">
        <h1>系统设置</h1>
        <div class="system-controls">
          <button id="saveSettingsBtn" class="btn btn-primary">保存设置</button>
          <button id="resetSettingsBtn" class="btn btn-secondary">重置</button>
          <button id="backupBtn" class="btn btn-secondary">备份系统</button>
        </div>
      </header>

      <div class="system-content">
        <div class="system-tabs">
          <button class="tab-btn active" data-tab="general">通用设置</button>
          <button class="tab-btn" data-tab="performance">性能配置</button>
          <button class="tab-btn" data-tab="security">安全配置</button>
          <button class="tab-btn" data-tab="maintenance">维护工具</button>
        </div>

        <div class="tab-content">
          <div id="generalTab" class="tab-pane active">
            <div class="settings-section">
              <h2>通用设置</h2>

              <div class="setting-group">
                <h3>基本信息</h3>
                <div class="setting-item">
                  <label>系统名称:</label>
                  <input type="text" id="systemName" placeholder="YLAI-AUTO-PLATFORM">
                </div>
                <div class="setting-item">
                  <label>系统版本:</label>
                  <input type="text" id="systemVersion" value="3.2.0" readonly>
                </div>
                <div class="setting-item">
                  <label>管理员邮箱:</label>
                  <input type="email" id="adminEmail" placeholder="admin@example.com">
                </div>
              </div>

              <div class="setting-group">
                <h3>界面设置</h3>
                <div class="setting-item">
                  <label>主题:</label>
                  <select id="theme">
                    <option value="light">浅色</option>
                    <option value="dark">深色</option>
                    <option value="auto">自动</option>
                  </select>
                </div>
                <div class="setting-item">
                  <label>语言:</label>
                  <select id="language">
                    <option value="zh-CN">中文(简体)</option>
                    <option value="zh-TW">中文(繁体)</option>
                    <option value="en-US">English</option>
                  </select>
                </div>
                <div class="setting-item">
                  <label>每页显示数量:</label>
                  <input type="number" id="pageSize" value="20" min="10" max="100">
                </div>
              </div>
            </div>
          </div>

          <div id="performanceTab" class="tab-pane">
            <div class="settings-section">
              <h2>性能配置</h2>

              <div class="setting-group">
                <h3>缓存配置</h3>
                <div class="setting-item">
                  <label>缓存类型:</label>
                  <select id="cacheType">
                    <option value="memory">内存缓存</option>
                    <option value="redis">Redis缓存</option>
                  </select>
                </div>
                <div class="setting-item">
                  <label>缓存过期时间(秒):</label>
                  <input type="number" id="cacheTTL" value="3600" min="60">
                </div>
                <div class="setting-item">
                  <label>最大缓存大小:</label>
                  <input type="number" id="maxCacheSize" value="1000" min="100">
                </div>
              </div>

              <div class="setting-group">
                <h3>并发控制</h3>
                <div class="setting-item">
                  <label>最大并发请求:</label>
                  <input type="number" id="maxConcurrency" value="10" min="1" max="50">
                </div>
                <div class="setting-item">
                  <label>请求超时时间(秒):</label>
                  <input type="number" id="requestTimeout" value="30" min="5" max="300">
                </div>
              </div>

              <div class="setting-group">
                <h3>数据库优化</h3>
                <div class="setting-item">
                  <label>连接池大小:</label>
                  <input type="number" id="dbPoolSize" value="10" min="1" max="100">
                </div>
                <div class="setting-item">
                  <label>查询缓存:</label>
                  <input type="checkbox" id="queryCache" checked>
                </div>
              </div>
            </div>
          </div>

          <div id="securityTab" class="tab-pane">
            <div class="settings-section">
              <h2>安全配置</h2>

              <div class="setting-group">
                <h3>认证设置</h3>
                <div class="setting-item">
                  <label>会话超时(分钟):</label>
                  <input type="number" id="sessionTimeout" value="60" min="5" max="480">
                </div>
                <div class="setting-item">
                  <label>密码最小长度:</label>
                  <input type="number" id="minPasswordLength" value="8" min="6" max="32">
                </div>
                <div class="setting-item">
                  <label>启用双因子认证:</label>
                  <input type="checkbox" id="enable2FA">
                </div>
              </div>

              <div class="setting-group">
                <h3>访问控制</h3>
                <div class="setting-item">
                  <label>允许IP白名单:</label>
                  <textarea id="ipWhitelist" placeholder="每行一个IP地址或CIDR" rows="3"></textarea>
                </div>
                <div class="setting-item">
                  <label>启用IP黑名单:</label>
                  <input type="checkbox" id="enableBlacklist">
                </div>
              </div>
            </div>
          </div>

          <div id="maintenanceTab" class="tab-pane">
            <div class="settings-section">
              <h2>维护工具</h2>

              <div class="maintenance-actions">
                <div class="action-group">
                  <h3>数据维护</h3>
                  <button id="clearCacheBtn" class="btn btn-warning">清理缓存</button>
                  <button id="optimizeDbBtn" class="btn btn-secondary">优化数据库</button>
                  <button id="exportDataBtn" class="btn btn-secondary">导出数据</button>
                </div>

                <div class="action-group">
                  <h3>系统维护</h3>
                  <button id="restartServicesBtn" class="btn btn-danger">重启服务</button>
                  <button id="updateSystemBtn" class="btn btn-primary">系统更新</button>
                  <button id="viewLogsBtn" class="btn btn-secondary">查看日志</button>
                </div>

                <div class="action-group">
                  <h3>备份恢复</h3>
                  <button id="createBackupBtn" class="btn btn-primary">创建备份</button>
                  <button id="restoreBackupBtn" class="btn btn-warning">恢复备份</button>
                  <button id="cleanupBackupsBtn" class="btn btn-secondary">清理旧备份</button>
                </div>
              </div>

              <div class="system-info">
                <h3>系统信息</h3>
                <div id="systemInfo" class="info-display">
                  <div class="loading">加载系统信息中...</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `);

  // Bind events
  const saveSettingsBtn = $('saveSettingsBtn');
  const resetSettingsBtn = $('resetSettingsBtn');
  const backupBtn = $('backupBtn');
  const tabBtns = document.querySelectorAll('.tab-btn');

  // Maintenance buttons
  const clearCacheBtn = $('clearCacheBtn');
  const optimizeDbBtn = $('optimizeDbBtn');
  const exportDataBtn = $('exportDataBtn');
  const restartServicesBtn = $('restartServicesBtn');
  const updateSystemBtn = $('updateSystemBtn');
  const viewLogsBtn = $('viewLogsBtn');
  const createBackupBtn = $('createBackupBtn');
  const restoreBackupBtn = $('restoreBackupBtn');
  const cleanupBackupsBtn = $('cleanupBackupsBtn');

  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('click', () => saveSettings());
  }

  if (resetSettingsBtn) {
    resetSettingsBtn.addEventListener('click', () => resetSettings());
  }

  if (backupBtn) {
    backupBtn.addEventListener('click', () => createBackup());
  }

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // Maintenance event listeners
  if (clearCacheBtn) {
    clearCacheBtn.addEventListener('click', () => clearCache());
  }

  if (optimizeDbBtn) {
    optimizeDbBtn.addEventListener('click', () => optimizeDatabase());
  }

  if (exportDataBtn) {
    exportDataBtn.addEventListener('click', () => exportData());
  }

  if (restartServicesBtn) {
    restartServicesBtn.addEventListener('click', () => restartServices());
  }

  if (updateSystemBtn) {
    updateSystemBtn.addEventListener('click', () => updateSystem());
  }

  if (viewLogsBtn) {
    viewLogsBtn.addEventListener('click', () => viewLogs());
  }

  if (createBackupBtn) {
    createBackupBtn.addEventListener('click', () => createBackup());
  }

  if (restoreBackupBtn) {
    restoreBackupBtn.addEventListener('click', () => restoreBackup());
  }

  if (cleanupBackupsBtn) {
    cleanupBackupsBtn.addEventListener('click', () => cleanupBackups());
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
  if (tabName === 'maintenance') {
    loadSystemInfo();
  }
}

async function loadSettings() {
  try {
    const settings = await fetchJSON('/api/system/settings');
    currentSettings = settings.data || {};
    populateSettingsForm(currentSettings);
  } catch (error) {
    showToastSafe('加载设置失败: ' + error.message, 'error');
    // Load default settings
    populateSettingsForm({});
  }
}

function populateSettingsForm(settings) {
  // General settings
  const systemName = $('systemName');
  const adminEmail = $('adminEmail');
  const theme = $('theme');
  const language = $('language');
  const pageSize = $('pageSize');

  if (systemName) systemName.value = settings.system_name || '';
  if (adminEmail) adminEmail.value = settings.admin_email || '';
  if (theme) theme.value = settings.theme || 'light';
  if (language) language.value = settings.language || 'zh-CN';
  if (pageSize) pageSize.value = settings.page_size || 20;

  // Performance settings
  const cacheType = $('cacheType');
  const cacheTTL = $('cacheTTL');
  const maxCacheSize = $('maxCacheSize');
  const maxConcurrency = $('maxConcurrency');
  const requestTimeout = $('requestTimeout');
  const dbPoolSize = $('dbPoolSize');
  const queryCache = $('queryCache');

  if (cacheType) cacheType.value = settings.cache_type || 'memory';
  if (cacheTTL) cacheTTL.value = settings.cache_ttl || 3600;
  if (maxCacheSize) maxCacheSize.value = settings.max_cache_size || 1000;
  if (maxConcurrency) maxConcurrency.value = settings.max_concurrency || 10;
  if (requestTimeout) requestTimeout.value = settings.request_timeout || 30;
  if (dbPoolSize) dbPoolSize.value = settings.db_pool_size || 10;
  if (queryCache) queryCache.checked = settings.query_cache !== false;

  // Security settings
  const sessionTimeout = $('sessionTimeout');
  const minPasswordLength = $('minPasswordLength');
  const enable2FA = $('enable2FA');
  const ipWhitelist = $('ipWhitelist');
  const enableBlacklist = $('enableBlacklist');

  if (sessionTimeout) sessionTimeout.value = settings.session_timeout || 60;
  if (minPasswordLength) minPasswordLength.value = settings.min_password_length || 8;
  if (enable2FA) enable2FA.checked = settings.enable_2fa || false;
  if (ipWhitelist) ipWhitelist.value = (settings.ip_whitelist || []).join('\n');
  if (enableBlacklist) enableBlacklist.checked = settings.enable_blacklist || false;
}

async function saveSettings() {
  const newSettings = collectSettingsFromForm();

  try {
    await fetchJSON('/api/system/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSettings)
    });
    currentSettings = { ...currentSettings, ...newSettings };
    showToastSafe('设置保存成功', 'success');
  } catch (error) {
    showToastSafe('保存设置失败: ' + error.message, 'error');
  }
}

function collectSettingsFromForm() {
  return {
    // General
    system_name: $('systemName')?.value || '',
    admin_email: $('adminEmail')?.value || '',
    theme: $('theme')?.value || 'light',
    language: $('language')?.value || 'zh-CN',
    page_size: parseInt($('pageSize')?.value) || 20,

    // Performance
    cache_type: $('cacheType')?.value || 'memory',
    cache_ttl: parseInt($('cacheTTL')?.value) || 3600,
    max_cache_size: parseInt($('maxCacheSize')?.value) || 1000,
    max_concurrency: parseInt($('maxConcurrency')?.value) || 10,
    request_timeout: parseInt($('requestTimeout')?.value) || 30,
    db_pool_size: parseInt($('dbPoolSize')?.value) || 10,
    query_cache: $('queryCache')?.checked || false,

    // Security
    session_timeout: parseInt($('sessionTimeout')?.value) || 60,
    min_password_length: parseInt($('minPasswordLength')?.value) || 8,
    enable_2fa: $('enable2FA')?.checked || false,
    ip_whitelist: ($('ipWhitelist')?.value || '').split('\n').filter(ip => ip.trim()),
    enable_blacklist: $('enableBlacklist')?.checked || false
  };
}

function resetSettings() {
  if (confirm('确定要重置所有设置为默认值吗？此操作不可撤销。')) {
    populateSettingsForm({});
    showToastSafe('设置已重置为默认值，请点击保存以应用', 'info');
  }
}

async function loadSystemInfo() {
  const systemInfo = $('systemInfo');
  if (!systemInfo) return;

  try {
    const info = await fetchJSON('/api/system/health');
    systemInfo.innerHTML = `
      <div class="info-item">
        <span class="label">系统状态:</span>
        <span class="value ${info.status === 'ok' ? 'healthy' : 'unhealthy'}">${info.status === 'ok' ? '正常' : '异常'}</span>
      </div>
      <div class="info-item">
        <span class="label">运行时间:</span>
        <span class="value">${info.uptime || '未知'}</span>
      </div>
      <div class="info-item">
        <span class="label">版本:</span>
        <span class="value">${info.version || '未知'}</span>
      </div>
      <div class="info-item">
        <span class="label">内存使用:</span>
        <span class="value">${info.memory_usage || '未知'}</span>
      </div>
      <div class="info-item">
        <span class="label">磁盘使用:</span>
        <span class="value">${info.disk_usage || '未知'}</span>
      </div>
    `;
  } catch (error) {
    systemInfo.innerHTML = `<div class="error">加载系统信息失败: ${error.message}</div>`;
  }
}

// Maintenance functions
async function clearCache() {
  try {
    await fetchJSON('/api/system/cache/clear', { method: 'POST' });
    showToastSafe('缓存清理成功', 'success');
  } catch (error) {
    showToastSafe('缓存清理失败: ' + error.message, 'error');
  }
}

async function optimizeDatabase() {
  try {
    await fetchJSON('/api/system/db/optimize', { method: 'POST' });
    showToastSafe('数据库优化完成', 'success');
  } catch (error) {
    showToastSafe('数据库优化失败: ' + error.message, 'error');
  }
}

async function exportData() {
  try {
    const response = await fetch('/api/system/data/export', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    });
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `system_data_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
    showToastSafe('数据导出成功', 'success');
  } catch (error) {
    showToastSafe('数据导出失败: ' + error.message, 'error');
  }
}

async function restartServices() {
  if (!confirm('确定要重启所有服务吗？这将导致短暂的服务中断。')) return;

  try {
    await fetchJSON('/api/system/services/restart', { method: 'POST' });
    showToastSafe('服务重启成功', 'success');
  } catch (error) {
    showToastSafe('服务重启失败: ' + error.message, 'error');
  }
}

async function updateSystem() {
  try {
    const result = await fetchJSON('/api/system/update', { method: 'POST' });
    showToastSafe('系统更新完成，请重启服务', 'success');
  } catch (error) {
    showToastSafe('系统更新失败: ' + error.message, 'error');
  }
}

function viewLogs() {
  window.open('/pages/logs.html', '_blank');
}

async function createBackup() {
  try {
    const result = await fetchJSON('/api/system/backup', { method: 'POST' });
    showToastSafe('备份创建成功', 'success');
  } catch (error) {
    showToastSafe('备份创建失败: ' + error.message, 'error');
  }
}

async function restoreBackup() {
  const backupFile = prompt('请输入备份文件名:');
  if (!backupFile) return;

  try {
    await fetchJSON('/api/system/restore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ backup_file: backupFile })
    });
    showToastSafe('备份恢复成功', 'success');
  } catch (error) {
    showToastSafe('备份恢复失败: ' + error.message, 'error');
  }
}

async function cleanupBackups() {
  try {
    await fetchJSON('/api/system/backups/cleanup', { method: 'POST' });
    showToastSafe('旧备份清理完成', 'success');
  } catch (error) {
    showToastSafe('清理备份失败: ' + error.message, 'error');
  }
}

export async function mount(root, options = {}) {
  console.log('System module mounting...');
  renderSystemDashboard();
  await loadSettings();
  return { root, options };
}

export default mount;

// Keep the registry part for backward compatibility
export const systemModule = {
  id: 'module.system',
  title: '系统设置',
  node: 'node.system',
  routes: {
    get: { method: 'GET', path: '/api/system/settings' },
    update: { method: 'POST', path: '/api/system/settings' },
    health: { method: 'GET', path: '/api/system/health' },
    backup: { method: 'POST', path: '/api/system/backup' },
    restore: { method: 'POST', path: '/api/system/restore' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
