export default {
  id: 'module.challenge',
  title: '破译挑战',
  node: 'node.challenge',
  routes: {
    create: { method: 'POST', path: '/api/challenge/create' },
    run: { method: 'POST', path: '/api/challenge/run/:id' },
    status: { method: 'GET', path: '/api/challenge/status/:id' },
    report: { method: 'GET', path: '/api/challenge/report/:id' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
