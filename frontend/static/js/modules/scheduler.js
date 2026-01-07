export default {
  id: 'module.scheduler',
  title: '智能调度',
  node: 'node.scheduler',
  routes: {
    start: { method: 'POST', path: '/api/scheduler/start' },
    stop: { method: 'POST', path: '/api/scheduler/stop' },
    status: { method: 'GET', path: '/api/scheduler/status' },
    aiRegister: { method: 'POST', path: '/api/ai/register' },
    pipeline: { method: 'POST', path: '/api/ai/pipeline' },
    dispatch: { method: 'POST', path: '/api/crawler/dispatch' },
    fallback: { method: 'POST', path: '/api/scheduler/fallback' },
  },
  actions: {
    async start(services, body) { return services.http.post(this.routes.start.path, body); },
    async stop(services) { return services.http.post(this.routes.stop.path, {}); },
    async getStatus(services) { return services.http.get(this.routes.status.path); },
  },
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
