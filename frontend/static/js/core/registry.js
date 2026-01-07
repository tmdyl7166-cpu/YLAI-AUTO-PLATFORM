const registry = new Map();

function normalizeModule(mod) {
  const m = mod || {};
  const id = m.id || m.name || m.node || 'module.unknown';
  return {
    id,
    title: m.title || id,
    node: m.node || id.replace('module.', 'node.'),
    routes: m.routes || {},
    actions: m.actions || {},
    validators: m.validators || {},
    init: m.init || (() => ({ ready: true })),
  };
}

// auto-load placeholder modules (1.1–1.9)
try {
  const modules = [
    await import('../modules/params.js'),
    await import('../modules/scheduler.js'),
    await import('../modules/crawler.js'),
    await import('../modules/enum.js'),
    await import('../modules/recognize.js'),
    await import('../modules/crack.js'),
    await import('../modules/auto.js'),
    await import('../modules/logs.js'),
    await import('../modules/workflow.js'),
    await import('../modules/ai.js'),
    await import('../modules/xparse.js'),
    await import('../modules/anti.js'),
    await import('../modules/limit.js'),
    await import('../modules/challenge.js'),
    await import('../modules/system.js'),
    await import('../modules/rbac.js'),
    await import('../modules/docs.js'),
    await import('../modules/backend.js'),
    await import('../modules/train.js'),
    await import('../modules/fastapi.js'),
    await import('../modules/security.js'),
  ];
  modules.forEach(m => m.default && m.default.init && m.default.init({
    register: (name, mod) => registry.set(String(name), normalizeModule(mod))
  }));
} catch (e) {
  // ignore load errors in placeholder phase
}

export function register(name, module) {
  registry.set(String(name), normalizeModule(module));
}

export function getModule(name) {
  return registry.get(String(name));
}

export function listModules() {
  return Array.from(registry.keys());
}
