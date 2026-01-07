export default {
  id: 'module.params',
  title: '参数部署',
  node: 'node.params',
  routes: {
    getConfig: { method: 'GET', path: '/api/params/config' },
    saveConfig: { method: 'POST', path: '/api/params/config' },
    validate: { method: 'POST', path: '/api/params/validate' },
    targets: { method: 'GET', path: '/api/params/targets' },
    riskCheck: { method: 'POST', path: '/api/params/risk-check' },
    rankPreview: { method: 'POST', path: '/api/params/rank-preview' },
    save: { method: 'POST', path: '/api/params/save' },
    load: { method: 'GET', path: '/api/params/load' },
    health: { method: 'GET', path: '/api/health' },
    triggerEvent: { method: 'POST', path: '/api/events/trigger' },
  },
  actions: {
    async fetchConfig(services, params) {
      return services.http.get(this.routes.getConfig.path, params);
    },
    async pushConfig(services, body) {
      return services.http.post(this.routes.saveConfig.path, body);
    },
  },
  validators: {
    range(body) { return true; },
    proxyConnectivity(body) { return true; },
  },
  init(registry) { registry.register(this.id, this); }
};
