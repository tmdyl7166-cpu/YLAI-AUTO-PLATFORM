// Login module: handles user authentication
// Ensure CSS via link tag (avoid treating CSS as JS module)
function ensureStyles(){
  const href = '/static/css/modules/login.module.css?v=__ASSET_VERSION__';
  const existed = Array.from(document.styleSheets||[]).some(ss=> ss.href && ss.href.includes('/static/css/modules/login.module.css'));
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

async function handleLogin(event) {
  event.preventDefault();
  const username = $('username').value.trim();
  const password = $('password').value.trim();

  if (!username || !password) {
    showToastSafe('请输入用户名和密码', 'error');
    return;
  }

  try {
    const response = await fetchJSON('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (response.access_token) {
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('user_role', response.role);
      showToastSafe('登录成功', 'success');
      // Redirect to index page
      setTimeout(() => window.location.href = '/pages/index.html', 1000);
    }
  } catch (error) {
    showToastSafe('登录失败: ' + error.message, 'error');
  }
}

function renderLoginForm() {
  ensureStyles();
  const root = $('app-root');
  if (!root) return;

  root.innerHTML = '';
  root.appendChild(html`
    <div class="login-container">
      <div class="login-card">
        <h1>YLAI 自动化平台</h1>
        <p class="login-subtitle">请登录以继续</p>

        <form id="login-form" class="login-form">
          <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" name="username" required placeholder="输入用户名">
          </div>

          <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" name="password" required placeholder="输入密码">
          </div>

          <button type="submit" class="btn btn-primary login-btn">登录</button>
        </form>

        <div class="login-info">
          <p>默认账户:</p>
          <ul>
            <li>admin / admin (管理员)</li>
            <li>yeling / yeling (超级管理员)</li>
            <li>yangyang / yangyang (普通用户)</li>
          </ul>
        </div>
      </div>
    </div>
  `);

  // Bind form submit
  const form = $('login-form');
  if (form) {
    form.addEventListener('submit', handleLogin);
  }
}

export async function mount(root, options = {}) {
  console.log('Login module mounting...');
  renderLoginForm();
  return { root, options };
}

export default mount;