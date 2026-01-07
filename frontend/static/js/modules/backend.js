export default {
  id: 'module.backend',
  title: '后端控制',
  node: 'node.backend',
  routes: {
    toggle: { method: 'POST', path: '/api/backend/toggle' },
    status: { method: 'GET', path: '/api/backend/status' },
    logs: { method: 'GET', path: '/api/backend/logs' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
