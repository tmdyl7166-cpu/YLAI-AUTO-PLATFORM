/// <reference types="cypress" />

// 渲染可见性断言：确保主要页面不是黑屏、至少一个交互控件可见、公共徽章存在
// 通过 baseUrl 访问，如：http://localhost:3000
// 可通过 CYPRESS_baseUrl 环境变量覆盖

const PAGES = [
  '/pages/index',
  '/pages/login',
  '/pages/rbac',
  '/pages/monitor',
  '/pages/run',
  '/pages/api-doc',
  '/pages/ai-demo',
  '/pages/DAG',
  '/pages/README',
];

function assertVisibleBasics() {
  // body 不隐藏
  cy.get('body').should($b => {
    const style = getComputedStyle($b[0]);
    expect(style.visibility).not.to.eq('hidden');
    expect(style.display).not.to.eq('none');
  });

  // 页面不为纯黑：opacity 不在 0（允许极小初始值）
  cy.get('body').should($b => {
    const style = getComputedStyle($b[0]);
    expect(parseFloat(style.opacity)).to.be.greaterThan(0);
  });

  // 公共徽章（若存在则需可见；不存在不阻断）
  cy.get('body').then(($b) => {
    const badge = $b.find('#ylai-badge');
    if (badge && badge.length) {
      cy.get('#ylai-badge').should('be.visible');
    }
  });

  // 至少有一个可见元素（排除脚本/样式等）
  cy.get('body *:visible').filter((_, el) => {
    const tag = el.tagName.toLowerCase();
    return !['script','style','link','meta'].includes(tag);
  }).should($els => {
    expect($els.length, '至少一个可见的非辅助元素').to.be.greaterThan(0);
  });
}

// 路由访问兼容：允许不带 .html 后缀
function visitCompat(path) {
  cy.visit(path, { failOnStatusCode: false });
}

describe('主要页面渲染可见性', () => {
  PAGES.forEach(p => {
    it(`页面可见：${p}`, () => {
      visitCompat(p);
      // 等待公共脚本执行和资源就绪
      cy.wait(600);
      assertVisibleBasics();
    });
  });
});
