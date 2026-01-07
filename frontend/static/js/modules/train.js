export default {
  id: 'module.train',
  title: 'AI训练',
  node: 'node.train',
  routes: {
    create: { method: 'POST', path: '/api/train/tasks' },
    run: { method: 'POST', path: '/api/train/run/:id' },
    status: { method: 'GET', path: '/api/train/status/:id' },
    eval: { method: 'GET', path: '/api/train/eval/:id' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
