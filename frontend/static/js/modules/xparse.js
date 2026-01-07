export default {
  id: 'module.xparse',
  title: '交叉解析',
  node: 'node.xparse',
  routes: {
    create: { method: 'POST', path: '/api/xparse/tasks' },
    run: { method: 'POST', path: '/api/xparse/run/:id' },
    status: { method: 'GET', path: '/api/xparse/status/:id' },
    result: { method: 'GET', path: '/api/xparse/result/:id' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
