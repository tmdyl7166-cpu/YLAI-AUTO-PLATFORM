export default {
  id: 'module.fastapi',
  title: 'FastAPI服务联动',
  node: 'node.fastapi',
  routes: {
    register: { method: 'POST', path: '/api/fastapi/register' },
    pipeline: { method: 'POST', path: '/api/fastapi/pipeline' },
    health: { method: 'GET', path: '/api/fastapi/health' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
