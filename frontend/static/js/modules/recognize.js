export default {
  id: 'module.recognize',
  title: '识别任务',
  node: 'node.recognize',
  routes: {
    submit: { method: 'POST', path: '/api/recognize/submit' },
    status: { method: 'GET', path: '/api/recognize/status/:id' },
    trace: { method: 'GET', path: '/api/recognize/trace/:id' },
    netinfo: { method: 'GET', path: '/api/netinfo' },
    orgLookup: { method: 'GET', path: '/api/org/lookup' },
    socialAggregate: { method: 'GET', path: '/api/social/aggregate' },
    collab: { method: 'POST', path: '/api/recognize/collab' },
    clueAggregate: { method: 'GET', path: '/api/clue/aggregate' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
