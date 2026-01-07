export default {
  id: 'module.crawler',
  title: '采集任务',
  node: 'node.crawler',
  routes: {
    list: { method: 'GET', path: '/api/crawler/tasks' },
    create: { method: 'POST', path: '/api/crawler/tasks' },
    validate: { method: 'POST', path: '/api/crawler/validate' },
    detail: { method: 'GET', path: '/api/crawler/tasks/:id' },
    start: { method: 'POST', path: '/api/crawler/tasks/:id/start' },
    stop: { method: 'POST', path: '/api/crawler/tasks/:id/stop' },
  },
  actions: {
    async list(services, params) { return services.http.get(this.routes.list.path, params); },
    async create(services, body) { return services.http.post(this.routes.create.path, body); },
  },
  validators: {
    form(fields) { return true; }
  },
  init(registry) { registry.register(this.id, this); }
};
