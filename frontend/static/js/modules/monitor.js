// Monitor module: system monitoring and metrics display
function ensureStyles(){
  const href = '/static/css/modules/monitor.module.css?v=__ASSET_VERSION__';
  const existed = Array.from(document.styleSheets||[]).some(ss=> ss.href && ss.href.includes('/static/css/modules/monitor.module.css'));
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

let metricsInterval = null;

function renderMonitorDashboard() {
  ensureStyles();
  const root = $('app-root');
  if (!root) return;

  root.innerHTML = '';
  root.appendChild(html`
    <div class="monitor-dashboard">
      <header class="monitor-header">
        <h1>系统监控</h1>
        <div class="monitor-controls">
          <button id="refreshBtn" class="btn btn-primary">刷新</button>
          <button id="autoRefreshBtn" class="btn btn-secondary">自动刷新</button>
          <span id="lastUpdate" class="last-update">最后更新: --</span>
        </div>
      </header>

      <div class="metrics-grid">
        <div class="metric-card">
          <h3>系统状态</h3>
          <div id="systemStatus" class="status-indicator">
            <div class="status-item">
              <span class="label">后端服务:</span>
              <span id="backendStatus" class="status unknown">检查中...</span>
            </div>
            <div class="status-item">
              <span class="label">缓存服务:</span>
              <span id="cacheStatus" class="status unknown">检查中...</span>
            </div>
            <div class="status-item">
              <span class="label">数据库:</span>
              <span id="dbStatus" class="status unknown">检查中...</span>
            </div>
          </div>
        </div>

        <div class="metric-card">
          <h3>性能指标</h3>
          <div id="performanceMetrics" class="metrics-display">
            <div class="metric-item">
              <span class="label">CPU使用率:</span>
              <span id="cpuUsage" class="value">--%</span>
            </div>
            <div class="metric-item">
              <span class="label">内存使用:</span>
              <span id="memoryUsage" class="value">--MB</span>
            </div>
            <div class="metric-item">
              <span class="label">活跃连接:</span>
              <span id="activeConnections" class="value">--</span>
            </div>
          </div>
        </div>

        <div class="metric-card">
          <h3>脚本统计</h3>
          <div id="scriptStats" class="stats-display">
            <div class="stat-item">
              <span class="label">已注册脚本:</span>
              <span id="scriptCount" class="value">--</span>
            </div>
            <div class="stat-item">
              <span class="label">运行中任务:</span>
              <span id="runningTasks" class="value">--</span>
            </div>
            <div class="stat-item">
              <span class="label">完成任务:</span>
              <span id="completedTasks" class="value">--</span>
            </div>
          </div>
        </div>

        <div class="metric-card">
          <h3>API统计</h3>
          <div id="apiStats" class="stats-display">
            <div class="stat-item">
              <span class="label">总请求数:</span>
              <span id="totalRequests" class="value">--</span>
            </div>
            <div class="stat-item">
              <span class="label">成功率:</span>
              <span id="successRate" class="value">--%</span>
            </div>
            <div class="stat-item">
              <span class="label">平均响应时间:</span>
              <span id="avgResponseTime" class="value">--ms</span>
            </div>
          </div>
        </div>
      </div>

      <div class="logs-section">
        <h2>系统日志</h2>
        <div id="logsContainer" class="logs-container">
          <div class="log-entry loading">加载日志中...</div>
        </div>
      </div>
    </div>
  `);

  // Bind events
  const refreshBtn = $('refreshBtn');
  const autoRefreshBtn = $('autoRefreshBtn');

  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => loadMetrics());
  }

  if (autoRefreshBtn) {
    autoRefreshBtn.addEventListener('click', () => toggleAutoRefresh());
  }
}

async function loadMetrics() {
  try {
    // Load health status
    const health = await fetchJSON('/health');
    updateHealthStatus(health);

    // Load scripts
    const scripts = await fetchJSON('/api/modules');
    updateScriptStats(scripts);

    // Load logs (if available)
    loadLogs();

    // Update timestamp
    const lastUpdate = $('lastUpdate');
    if (lastUpdate) {
      lastUpdate.textContent = `最后更新: ${new Date().toLocaleTimeString()}`;
    }

  } catch (error) {
    showToastSafe('加载监控数据失败: ' + error.message, 'error');
  }
}

function updateHealthStatus(health) {
  const backendStatus = $('backendStatus');
  const cacheStatus = $('cacheStatus');
  const dbStatus = $('dbStatus');

  if (backendStatus) {
    backendStatus.textContent = health.status === 'ok' ? '正常' : '异常';
    backendStatus.className = `status ${health.status === 'ok' ? 'healthy' : 'unhealthy'}`;
  }

  // Update cache and DB status based on health data
  if (cacheStatus && health.services?.cache) {
    const cacheHealthy = health.services.cache.available;
    cacheStatus.textContent = cacheHealthy ? '正常' : '异常';
    cacheStatus.className = `status ${cacheHealthy ? 'healthy' : 'unhealthy'}`;
  }

  if (dbStatus && health.services?.database) {
    const dbHealthy = health.services.database.available;
    dbStatus.textContent = dbHealthy ? '正常' : '异常';
    dbStatus.className = `status ${dbHealthy ? 'healthy' : 'unhealthy'}`;
  }
}

function updateScriptStats(scripts) {
  const scriptCount = $('scriptCount');
  if (scriptCount && scripts.data) {
    scriptCount.textContent = scripts.data.length;
  }
}

async function loadLogs() {
  const logsContainer = $('logsContainer');
  if (!logsContainer) return;

  try {
    // Try to load logs from WebSocket or API
    logsContainer.innerHTML = '<div class="log-entry">日志系统正在开发中...</div>';
  } catch (error) {
    logsContainer.innerHTML = '<div class="log-entry error">无法加载日志</div>';
  }
}

function toggleAutoRefresh() {
  const autoRefreshBtn = $('autoRefreshBtn');

  if (metricsInterval) {
    clearInterval(metricsInterval);
    metricsInterval = null;
    if (autoRefreshBtn) {
      autoRefreshBtn.textContent = '自动刷新';
      autoRefreshBtn.classList.remove('active');
    }
  } else {
    metricsInterval = setInterval(() => loadMetrics(), 5000); // 5 seconds
    if (autoRefreshBtn) {
      autoRefreshBtn.textContent = '停止自动刷新';
      autoRefreshBtn.classList.add('active');
    }
  }
}

export async function mount(root, options = {}) {
  console.log('Monitor module mounting...');
  renderMonitorDashboard();
  await loadMetrics();
  return { root, options };
}

export default mount;
