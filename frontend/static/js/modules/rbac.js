// RBAC module: Role-Based Access Control management
function ensureStyles(){
  const href = '/static/css/modules/rbac.module.css?v=__ASSET_VERSION__';
  const existed = Array.from(document.styleSheets||[]).some(ss=> ss.href && ss.href.includes('/static/css/modules/rbac.module.css'));
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

function renderRbacDashboard() {
  ensureStyles();
  const root = $('app-root');
  if (!root) return;

  root.innerHTML = '';
  root.appendChild(html`
    <div class="rbac-dashboard">
      <header class="rbac-header">
        <h1>权限管理 (RBAC)</h1>
        <div class="rbac-controls">
          <button id="refreshBtn" class="btn btn-primary">刷新</button>
        </div>
      </header>

      <div class="rbac-content">
        <div class="rbac-tabs">
          <button class="tab-btn active" data-tab="users">用户管理</button>
          <button class="tab-btn" data-tab="roles">角色管理</button>
          <button class="tab-btn" data-tab="policies">策略管理</button>
        </div>

        <div class="tab-content">
          <div id="usersTab" class="tab-pane active">
            <div class="tab-header">
              <h2>用户列表</h2>
              <button id="addUserBtn" class="btn btn-secondary">添加用户</button>
            </div>
            <div id="usersList" class="data-list">
              <div class="loading">加载用户列表中...</div>
            </div>
          </div>

          <div id="rolesTab" class="tab-pane">
            <div class="tab-header">
              <h2>角色列表</h2>
              <button id="addRoleBtn" class="btn btn-secondary">添加角色</button>
            </div>
            <div id="rolesList" class="data-list">
              <div class="loading">加载角色列表中...</div>
            </div>
          </div>

          <div id="policiesTab" class="tab-pane">
            <div class="tab-header">
              <h2>策略列表</h2>
              <button id="addPolicyBtn" class="btn btn-secondary">添加策略</button>
            </div>
            <div id="policiesList" class="data-list">
              <div class="loading">加载策略列表中...</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `);

  // Bind events
  const refreshBtn = $('refreshBtn');
  const tabBtns = document.querySelectorAll('.tab-btn');
  const addUserBtn = $('addUserBtn');
  const addRoleBtn = $('addRoleBtn');
  const addPolicyBtn = $('addPolicyBtn');

  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => loadRbacData());
  }

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  if (addUserBtn) {
    addUserBtn.addEventListener('click', () => showAddUserDialog());
  }

  if (addRoleBtn) {
    addRoleBtn.addEventListener('click', () => showAddRoleDialog());
  }

  if (addPolicyBtn) {
    addPolicyBtn.addEventListener('click', () => showAddPolicyDialog());
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

async function loadRbacData() {
  await Promise.all([
    loadTabData('users'),
    loadTabData('roles'),
    loadTabData('policies')
  ]);
}

async function loadTabData(tabName) {
  const listId = `${tabName}List`;
  const listDiv = $(listId);
  if (!listDiv) return;

  try {
    let data;
    switch (tabName) {
      case 'users':
        data = await fetchJSON('/api/rbac/users');
        renderUsersList(data.data || []);
        break;
      case 'roles':
        data = await fetchJSON('/api/rbac/roles');
        renderRolesList(data.data || []);
        break;
      case 'policies':
        data = await fetchJSON('/api/rbac/policies');
        renderPoliciesList(data.data || []);
        break;
    }
  } catch (error) {
    listDiv.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
  }
}

function renderUsersList(users) {
  const listDiv = $('usersList');
  if (!listDiv) return;

  if (!users || users.length === 0) {
    listDiv.innerHTML = '<div class="no-data">暂无用户</div>';
    return;
  }

  listDiv.innerHTML = '';
  users.forEach(user => {
    const item = document.createElement('div');
    item.className = 'data-item user-item';
    item.innerHTML = `
      <div class="item-info">
        <div class="item-title">${user.username}</div>
        <div class="item-meta">角色: ${user.roles?.join(', ') || '无'}</div>
      </div>
      <div class="item-actions">
        <button class="btn btn-sm" onclick="editUser('${user.id}')">编辑</button>
        <button class="btn btn-sm btn-danger" onclick="deleteUser('${user.id}')">删除</button>
      </div>
    `;
    listDiv.appendChild(item);
  });
}

function renderRolesList(roles) {
  const listDiv = $('rolesList');
  if (!listDiv) return;

  if (!roles || roles.length === 0) {
    listDiv.innerHTML = '<div class="no-data">暂无角色</div>';
    return;
  }

  listDiv.innerHTML = '';
  roles.forEach(role => {
    const item = document.createElement('div');
    item.className = 'data-item role-item';
    item.innerHTML = `
      <div class="item-info">
        <div class="item-title">${role.name}</div>
        <div class="item-meta">描述: ${role.description || '无'}</div>
      </div>
      <div class="item-actions">
        <button class="btn btn-sm" onclick="editRole('${role.id}')">编辑</button>
        <button class="btn btn-sm btn-danger" onclick="deleteRole('${role.id}')">删除</button>
      </div>
    `;
    listDiv.appendChild(item);
  });
}

function renderPoliciesList(policies) {
  const listDiv = $('policiesList');
  if (!listDiv) return;

  if (!policies || policies.length === 0) {
    listDiv.innerHTML = '<div class="no-data">暂无策略</div>';
    return;
  }

  listDiv.innerHTML = '';
  policies.forEach(policy => {
    const item = document.createElement('div');
    item.className = 'data-item policy-item';
    item.innerHTML = `
      <div class="item-info">
        <div class="item-title">${policy.name}</div>
        <div class="item-meta">资源: ${policy.resource}, 操作: ${policy.action}</div>
      </div>
      <div class="item-actions">
        <button class="btn btn-sm" onclick="editPolicy('${policy.id}')">编辑</button>
        <button class="btn btn-sm btn-danger" onclick="deletePolicy('${policy.id}')">删除</button>
      </div>
    `;
    listDiv.appendChild(item);
  });
}

function showAddUserDialog() {
  // Simple dialog implementation
  const dialog = document.createElement('div');
  dialog.className = 'modal-dialog';
  dialog.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h3>添加用户</h3>
        <button class="modal-close" onclick="this.closest('.modal-dialog').remove()">×</button>
      </div>
      <div class="modal-body">
        <form id="addUserForm">
          <div class="form-group">
            <label>用户名:</label>
            <input type="text" name="username" required>
          </div>
          <div class="form-group">
            <label>密码:</label>
            <input type="password" name="password" required>
          </div>
          <div class="form-group">
            <label>角色:</label>
            <select name="role" multiple>
              <option value="admin">管理员</option>
              <option value="user">普通用户</option>
            </select>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="this.closest('.modal-dialog').remove()">取消</button>
        <button class="btn btn-primary" onclick="submitAddUser()">添加</button>
      </div>
    </div>
  `;
  document.body.appendChild(dialog);
}

function showAddRoleDialog() {
  // Similar implementation for role dialog
  showToastSafe('角色管理功能开发中', 'info');
}

function showAddPolicyDialog() {
  // Similar implementation for policy dialog
  showToastSafe('策略管理功能开发中', 'info');
}

export async function mount(root, options = {}) {
  console.log('RBAC module mounting...');
  renderRbacDashboard();
  await loadRbacData();
  return { root, options };
}

export default mount;

// Keep the registry part for backward compatibility
export const rbacModule = {
  id: 'module.rbac',
  title: '权限管理',
  node: 'node.rbac',
  routes: {
    users: { method: 'GET', path: '/api/rbac/users' },
    roles: { method: 'GET', path: '/api/rbac/roles' },
    policies: { method: 'GET', path: '/api/rbac/policies' },
    bindRole: { method: 'POST', path: '/api/rbac/bind-role' },
    bindPolicy: { method: 'POST', path: '/api/rbac/bind-policy' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
