export default {
  id: 'module.limit',
  title: '极限突破',
  node: 'node.limit',
  routes: {
    config: { method: 'POST', path: '/api/limit/override/config' },
    toggle: { method: 'POST', path: '/api/limit/override/toggle' },
    run: { method: 'POST', path: '/api/limit/override/run' },
    report: { method: 'GET', path: '/api/limit/override/report/:id' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
