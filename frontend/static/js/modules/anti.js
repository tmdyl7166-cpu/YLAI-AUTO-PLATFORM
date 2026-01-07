export default {
  id: 'module.anti',
  title: '反追反穿',
  node: 'node.anti',
  routes: {
    config: { method: 'POST', path: '/api/anti/trace/config' },
    toggleBypass: { method: 'POST', path: '/api/anti/bypass/toggle' },
    run: { method: 'POST', path: '/api/anti/trace/run' },
    evaluate: { method: 'GET', path: '/api/anti/trace/evaluate' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
