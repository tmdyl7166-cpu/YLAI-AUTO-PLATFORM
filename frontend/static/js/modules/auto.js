export default {
  id: 'module.auto',
  title: '自动化状态',
  node: 'node.auto',
  routes: {
    overview: { method: 'GET', path: '/api/auto/overview' },
    progress: { method: 'GET', path: '/api/auto/progress' },
    securityLevels: { method: 'GET', path: '/api/auto/security-levels' },
    keywordStrategy: { method: 'POST', path: '/api/auto/keyword-strategy' },
    fastTask: { method: 'POST', path: '/api/auto/fast-task' },
    captcha: { method: 'POST', path: '/api/auto/captcha' },
    collect: { method: 'POST', path: '/api/auto/collect' },
    switchStrategy: { method: 'POST', path: '/api/auto/switch-strategy' },
    bypassProgress: { method: 'GET', path: '/api/auto/bypass-progress' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
