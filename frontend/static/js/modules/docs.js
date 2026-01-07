export default {
  id: 'module.docs',
  title: 'API接口文档',
  node: 'node.docs',
  routes: {
    spec: { method: 'GET', path: '/api/docs/spec' },
    sync: { method: 'POST', path: '/api/docs/sync' },
    health: { method: 'GET', path: '/api/docs/health' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
