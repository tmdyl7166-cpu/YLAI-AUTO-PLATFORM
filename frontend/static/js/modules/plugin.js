// Plugin Market module: plugin management interface
function ensureStyles(){
  const href = '/static/css/modules/plugin.module.css?v=__ASSET_VERSION__';
  const existed = Array.from(document.styleSheets||[]).some(ss=> ss.href && ss.href.includes('/static/css/modules/plugin.module.css'));
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

let pluginData = null;

function renderPluginDashboard() {
  ensureStyles();
  const root = $('app-root');
  if (!root) return;

  root.innerHTML = '';
  root.appendChild(html`
    <div class="plugin-dashboard">
      <header class="plugin-header">
        <h1>插件市场</h1>
        <div class="plugin-controls">
          <input type="text" id="searchInput" placeholder="搜索插件..." class="search-input">
          <select id="statusFilter" class="filter-select">
            <option value="">所有状态</option>
            <option value="installed">已安装</option>
            <option value="available">可用</option>
          </select>
          <select id="categoryFilter" class="filter-select">
            <option value="">所有分类</option>
            <option value="data_source">数据源</option>
            <option value="data_handler">数据处理器</option>
            <option value="output_processor">输出处理器</option>
            <option value="utility">工具</option>
          </select>
          <button id="refreshBtn" class="btn btn-primary">刷新</button>
          <button id="discoverBtn" class="btn btn-secondary">重新发现</button>
        </div>
      </header>

      <div class="plugin-content">
        <nav class="plugin-nav">
          <div class="plugin-tabs">
            <button id="installedTab" class="tab-btn active">已安装插件</button>
            <button id="availableTab" class="tab-btn">可用插件</button>
          </div>
          <div id="pluginList" class="plugin-list">
            <div class="loading">加载插件列表中...</div>
          </div>
        </nav>

        <main class="plugin-main">
          <div id="pluginDetail" class="plugin-detail">
            <div class="welcome-message">
              <h2>欢迎使用插件市场</h2>
              <p>选择左侧的插件查看详细信息</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  `);

  // Bind events
  const searchInput = $('searchInput');
  const statusFilter = $('statusFilter');
  const categoryFilter = $('categoryFilter');
  const refreshBtn = $('refreshBtn');
  const discoverBtn = $('discoverBtn');
  const installedTab = $('installedTab');
  const availableTab = $('availableTab');

  if (searchInput) {
    searchInput.addEventListener('input', () => filterPlugins());
  }

  if (statusFilter) {
    statusFilter.addEventListener('change', () => filterPlugins());
  }

  if (categoryFilter) {
    categoryFilter.addEventListener('change', () => filterPlugins());
  }

  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => loadPlugins());
  }

  if (discoverBtn) {
    discoverBtn.addEventListener('click', () => discoverPlugins());
  }

  if (installedTab) {
    installedTab.addEventListener('click', () => switchTab('installed'));
  }

  if (availableTab) {
    availableTab.addEventListener('click', () => switchTab('available'));
  }

  // Load initial data
  loadPlugins();
}

async function loadPlugins() {
  try {
    const data = await fetchJSON('/api/plugins');
    pluginData = data.data;
    renderPluginList();
  } catch (error) {
    console.error('Failed to load plugins:', error);
    showToastSafe('加载插件列表失败: ' + error.message, 'error');
    renderError('加载插件列表失败，请稍后重试');
  }
}

async function discoverPlugins() {
  try {
    await fetchJSON('/api/plugins/discover', { method: 'POST' });
    showToastSafe('插件发现完成', 'success');
    loadPlugins();
  } catch (error) {
    console.error('Failed to discover plugins:', error);
    showToastSafe('插件发现失败: ' + error.message, 'error');
  }
}

function switchTab(tab) {
  const installedTab = $('installedTab');
  const availableTab = $('availableTab');

  if (tab === 'installed') {
    installedTab.classList.add('active');
    availableTab.classList.remove('active');
  } else {
    availableTab.classList.add('active');
    installedTab.classList.remove('active');
  }

  renderPluginList(tab);
}

function renderPluginList(activeTab = 'installed') {
  if (!pluginData) return;

  const pluginList = $('pluginList');
  if (!pluginList) return;

  const plugins = activeTab === 'installed' ? pluginData.installed : pluginData.available;

  if (!plugins || plugins.length === 0) {
    pluginList.innerHTML = '<div class="no-plugins">暂无插件</div>';
    return;
  }

  pluginList.innerHTML = '';
  plugins.forEach(plugin => {
    const pluginItem = html`
      <div class="plugin-item" data-plugin-id="${plugin.id}">
        <div class="plugin-icon">
          <i class="icon-${plugin.category || 'utility'}"></i>
        </div>
        <div class="plugin-info">
          <h3 class="plugin-name">${plugin.name}</h3>
          <p class="plugin-description">${plugin.description || '暂无描述'}</p>
          <div class="plugin-meta">
            <span class="plugin-version">v${plugin.version || '1.0.0'}</span>
            <span class="plugin-category">${getCategoryName(plugin.category)}</span>
            ${activeTab === 'installed' ?
              '<span class="plugin-status installed">已安装</span>' :
              '<span class="plugin-status available">可用</span>'}
          </div>
        </div>
        <div class="plugin-actions">
          <button class="btn btn-sm btn-outline" onclick="showPluginDetail('${plugin.id}')">
            详情
          </button>
          ${activeTab === 'installed' ?
            `<button class="btn btn-sm btn-danger" onclick="uninstallPlugin('${plugin.id}')">
              卸载
            </button>` :
            `<button class="btn btn-sm btn-success" onclick="installPlugin('${plugin.id}')">
              安装
            </button>`}
        </div>
      </div>
    `;
    pluginList.appendChild(pluginItem);
  });

  // Bind click events
  pluginList.querySelectorAll('.plugin-item').forEach(item => {
    item.addEventListener('click', (e) => {
      if (!e.target.closest('.plugin-actions')) {
        const pluginId = item.dataset.pluginId;
        showPluginDetail(pluginId);
      }
    });
  });
}

function getCategoryName(category) {
  const categories = {
    'data_source': '数据源',
    'data_handler': '数据处理器',
    'output_processor': '输出处理器',
    'utility': '工具'
  };
  return categories[category] || '其他';
}

async function showPluginDetail(pluginId) {
  try {
    const data = await fetchJSON(`/api/plugins/${pluginId}`);
    const plugin = data.data;

    const pluginDetail = $('pluginDetail');
    if (!pluginDetail) return;

    pluginDetail.innerHTML = '';

    const isInstalled = pluginData.installed && pluginData.installed.some(p => p.id === pluginId);

    const detailContent = html`
      <div class="plugin-detail-content">
        <header class="plugin-detail-header">
          <div class="plugin-icon-large">
            <i class="icon-${plugin.category || 'utility'}"></i>
          </div>
          <div class="plugin-info-main">
            <h2>${plugin.name}</h2>
            <div class="plugin-meta">
              <span class="plugin-version">版本: ${plugin.version || '1.0.0'}</span>
              <span class="plugin-category">分类: ${getCategoryName(plugin.category)}</span>
              <span class="plugin-status ${isInstalled ? 'installed' : 'available'}">
                ${isInstalled ? '已安装' : '未安装'}
              </span>
            </div>
          </div>
          <div class="plugin-actions-main">
            ${isInstalled ?
              `<button class="btn btn-danger" onclick="uninstallPlugin('${pluginId}')">
                卸载插件
              </button>` :
              `<button class="btn btn-success" onclick="installPlugin('${pluginId}')">
                安装插件
              </button>`}
          </div>
        </header>

        <div class="plugin-description-full">
          <h3>插件描述</h3>
          <p>${plugin.description || '暂无详细描述'}</p>
        </div>

        ${plugin.capabilities && plugin.capabilities.length > 0 ? `
          <div class="plugin-capabilities">
            <h3>插件能力</h3>
            <div class="capabilities-list">
              ${plugin.capabilities.map(cap => `
                <div class="capability-item">
                  <h4>${cap.name}</h4>
                  <p>${cap.description || '暂无描述'}</p>
                  <button class="btn btn-sm btn-outline" onclick="executeCapability('${pluginId}', '${cap.name}')">
                    执行
                  </button>
                </div>
              `).join('')}
            </div>
          </div>
        ` : ''}

        <div class="plugin-details">
          <h3>详细信息</h3>
          <div class="details-grid">
            <div class="detail-item">
              <label>插件ID:</label>
              <span>${plugin.id}</span>
            </div>
            <div class="detail-item">
              <label>作者:</label>
              <span>${plugin.author || '未知'}</span>
            </div>
            <div class="detail-item">
              <label>许可证:</label>
              <span>${plugin.license || '未知'}</span>
            </div>
            <div class="detail-item">
              <label>主页:</label>
              <span>${plugin.homepage ? `<a href="${plugin.homepage}" target="_blank">${plugin.homepage}</a>` : '无'}</span>
            </div>
          </div>
        </div>
      </div>
    `;

    pluginDetail.appendChild(detailContent);
  } catch (error) {
    console.error('Failed to load plugin detail:', error);
    showToastSafe('加载插件详情失败: ' + error.message, 'error');
  }
}

async function installPlugin(pluginId) {
  try {
    await fetchJSON(`/api/plugins/${pluginId}/install`, { method: 'POST' });
    showToastSafe('插件安装成功', 'success');
    loadPlugins();
  } catch (error) {
    console.error('Failed to install plugin:', error);
    showToastSafe('插件安装失败: ' + error.message, 'error');
  }
}

async function uninstallPlugin(pluginId) {
  try {
    await fetchJSON(`/api/plugins/${pluginId}`, { method: 'DELETE' });
    showToastSafe('插件卸载成功', 'success');
    loadPlugins();
  } catch (error) {
    console.error('Failed to uninstall plugin:', error);
    showToastSafe('插件卸载失败: ' + error.message, 'error');
  }
}

async function executeCapability(pluginId, functionName) {
  try {
    const result = await fetchJSON(`/api/plugins/${pluginId}/${functionName}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    showToastSafe(`能力执行成功: ${JSON.stringify(result.data)}`, 'success');
  } catch (error) {
    console.error('Failed to execute capability:', error);
    showToastSafe('能力执行失败: ' + error.message, 'error');
  }
}

function filterPlugins() {
  const searchInput = $('searchInput');
  const statusFilter = $('statusFilter');
  const categoryFilter = $('categoryFilter');

  const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
  const statusValue = statusFilter ? statusFilter.value : '';
  const categoryValue = categoryFilter ? categoryFilter.value : '';

  const pluginItems = document.querySelectorAll('.plugin-item');

  pluginItems.forEach(item => {
    const pluginId = item.dataset.pluginId;
    const pluginName = item.querySelector('.plugin-name').textContent.toLowerCase();
    const pluginDesc = item.querySelector('.plugin-description').textContent.toLowerCase();

    let visible = true;

    // Search filter
    if (searchTerm && !pluginName.includes(searchTerm) && !pluginDesc.includes(searchTerm)) {
      visible = false;
    }

    // Status filter
    if (statusValue) {
      const isInstalled = pluginData.installed && pluginData.installed.some(p => p.id === pluginId);
      if (statusValue === 'installed' && !isInstalled) visible = false;
      if (statusValue === 'available' && isInstalled) visible = false;
    }

    // Category filter
    if (categoryValue) {
      const plugin = [...(pluginData.installed || []), ...(pluginData.available || [])].find(p => p.id === pluginId);
      if (plugin && plugin.category !== categoryValue) visible = false;
    }

    item.style.display = visible ? 'flex' : 'none';
  });
}

function renderError(message) {
  const pluginList = $('pluginList');
  if (pluginList) {
    pluginList.innerHTML = `<div class="error-message">${message}</div>`;
  }
}

// Export the mount function
window.mountPluginDashboard = renderPluginDashboard;