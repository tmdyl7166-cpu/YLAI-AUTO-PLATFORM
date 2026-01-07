export default {
  id: 'module.logs',
  title: '日志管理',
  node: 'node.logs',
  routes: {
    deploy: { method: 'GET', path: '/api/logs/deploy' },
    install: { method: 'GET', path: '/api/logs/install' },
    ipLogin: { method: 'GET', path: '/api/logs/ip-login' },
    usage: { method: 'GET', path: '/api/logs/usage' },
    cleanup: { method: 'POST', path: '/api/logs/cleanup' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
