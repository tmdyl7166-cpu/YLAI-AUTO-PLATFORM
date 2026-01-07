export default {
  id: 'module.workflow',
  title: '工作流部署',
  node: 'node.workflow',
  routes: {
    deploy: { method: 'POST', path: '/api/workflow/deploy' },
    runBasic1: { method: 'POST', path: '/api/workflow/run/basic1' },
    runBasic2: { method: 'POST', path: '/api/workflow/run/basic2' },
    runBasic3: { method: 'POST', path: '/api/workflow/run/basic3' },
    override: { method: 'POST', path: '/api/workflow/override' },
    runAdvanced: { method: 'POST', path: '/api/workflow/run/advanced' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
