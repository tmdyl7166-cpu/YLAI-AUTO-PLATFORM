export default {
  id: 'module.enum',
  title: '枚举任务',
  node: 'node.enum',
  routes: {
    list: { method: 'GET', path: '/api/enum/tasks' },
    binCheck: { method: 'POST', path: '/api/enum/bin-check' },
    gameCard: { method: 'POST', path: '/api/enum/game-card' },
    virtualCard: { method: 'POST', path: '/api/enum/virtual-card' },
    mnemonic: { method: 'POST', path: '/api/enum/mnemonic' },
    hexKey: { method: 'POST', path: '/api/enum/hex-key' },
    key32: { method: 'POST', path: '/api/enum/key32' },
    config: { method: 'POST', path: '/api/enum/config' },
    crossRun: { method: 'POST', path: '/api/enum/cross-run' },
    scan: { method: 'POST', path: '/api/enum/scan' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
