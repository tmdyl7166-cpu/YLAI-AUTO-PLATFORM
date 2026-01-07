// 验证登录来源标记与门禁：from_login 与 index_superadmin，以及 run 页导航锁定

describe('Auth Flow & Gating', () => {
  const BASE = 'http://127.0.0.1:8001';
  const ONLY_ADMIN = Cypress.env('ONLY_ADMIN') === 1 || Cypress.env('ONLY_ADMIN') === '1';
  const ONLY_LOGIN = Cypress.env('ONLY_LOGIN') === 1 || Cypress.env('ONLY_LOGIN') === '1';

  // 统一忽略非关键的第三方或良性异常，避免影响入口验证
  Cypress.on('uncaught:exception', (err) => {
    if (/ResizeObserver loop limit|Unexpected end of input/.test(err.message)) {
      return false;
    }
  });
  
  // 多策略选择器：按 data-testid、id、name、文本包含 依次尝试
  const getByAny = (labels, options = {}) => {
    const trySelectors = [];
    labels.forEach(l => {
      trySelectors.push(`[data-testid="${l}"]`);
      trySelectors.push(`#${l}`);
      trySelectors.push(`[name="${l}"]`);
    });
    // 通过文本匹配按钮/链接
    const textLabels = labels.filter(Boolean);
    return cy.then(() => {
      // 先尝试显式选择器
      for (const sel of trySelectors) {
        const el = Cypress.$(sel);
        if (el && el.length) {
          return cy.get(sel, options);
        }
      }
      // 再尝试文本包含（按钮/链接）
      for (const t of textLabels) {
        // 常见中文文案匹配：管理员登录/登录/提交/进入任务中心
        cy.log(`fallback contains: ${t}`);
        const candidates = ['button', 'a', '[role="button"]'];
        for (const c of candidates) {
          const el2 = Cypress.$(c).filter((_, e) => (e.innerText || '').includes(t));
          if (el2 && el2.length) {
            return cy.contains(c, t, options);
          }
        }
        // 全局文本 contains
        return cy.contains(t, options);
      }
      // 最后兜底：失败
      throw new Error(`Element not found by labels: ${JSON.stringify(labels)}`);
    });
  };

  beforeEach(() => {
    // 清理本地与会话存储
    cy.clearLocalStorage();
    cy.window().then(win => {
      win.sessionStorage.clear();
    });
  });

  it('Index 超管登录后可访问受限页且标记生效', function () {
    if (ONLY_LOGIN) {
      this.skip();
    }
    // 访问 index
    cy.visit(`${BASE}/pages/index.html`);
    // 优先使用测试辅助函数直接触发超管登录，减少对 UI 交互依赖
    cy.window().then(win => {
      if (typeof win.triggerAdminLogin === 'function') {
        win.triggerAdminLogin();
      } else {
        // 回退到按钮点击
        getByAny(['admin-login', '管理员登录', '进入任务中心', '登录']).click();
      }
    });
    // 验证标记
    cy.window().then(win => {
      expect(win.sessionStorage.getItem('index_superadmin')).to.eq('1');
      expect(win.localStorage.getItem('yl_user_role')).to.eq('superadmin');
    });
    // 访问受限页 api-doc
    cy.visit(`${BASE}/pages/api-doc.html`);
    cy.location('pathname').should('include', '/pages/api-doc.html');
    // 访问受限页 visual_pipeline
    cy.visit(`${BASE}/pages/visual_pipeline.html`);
    cy.location('pathname').should('include', '/pages/visual_pipeline.html');
  });

  it('Login 普通来源跳转 run 并设置 from_login，受限页重定向', function () {
    if (ONLY_ADMIN) {
      // 跳过该用例，当只验证超管场景
      this.skip();
    }
    // 访问 login
    cy.visit(`${BASE}/pages/login.html`);
    // 拦截可能的模块接口，以避免后端不稳定导致测试波动
    cy.intercept('GET', '/api/modules', { statusCode: 200, body: { modules: [] } }).as('modules');
    // 输入账号并登录（兼容 id/name/data-testid）
    getByAny(['login-username', 'username', 'user']).type('user');
    getByAny(['login-password', 'password', 'pass']).type('pass');
    getByAny(['login-submit', 'submit', '登录', '立即登录']).click();
    // 跳转到 run
    cy.location('pathname', { timeout: 5000 }).should('include', '/pages/run.html');
    // 验证 from_login 标记
    cy.window().then(win => {
      expect(win.sessionStorage.getItem('from_login')).to.eq('1');
    });
    // 尝试访问受限页，应重定向回 index
    cy.visit(`${BASE}/pages/api-doc.html`);
    cy.location('pathname').should('include', '/pages/index.html');
  });

  it('Run 页面导航锁定：拦截外链跳转', function () {
    if (ONLY_ADMIN) {
      // 跳过该用例，当只验证超管场景
      this.skip();
    }
    // 预设 from_login 来源并进入 run
    cy.visit(`${BASE}/pages/run.html`, {
      onBeforeLoad(win) {
        win.sessionStorage.setItem('from_login', '1');
      }
    });
    // 页面上应有被锁定的导航链接，点击后仍留在 run 页（兼容多选择器与文本）
    getByAny(['locked-link', '返回', '首页', 'index']).click({ force: true });
    cy.location('pathname').should('include', '/pages/run.html');
  });
});
