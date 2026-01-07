// stripped module (to be unified later)
void 0;
// 模块注册表：统一从 modules 目录装配页面逻辑
export const MODULES = {
  index: async () => (await import('./index.js')),
  'api-doc': async () => (await import('./api-doc.js')),
  run: async () => (await import('./run.js')),
  monitor: async () => (await import('./monitor.js')),
  'ai-demo': async () => (await import('./ai-demo.js')),
  visual_pipeline: async () => (await import('./visual_pipeline.js')),
  rbac: async () => (await import('./rbac.js')),
  params: async () => (await import('./params.js')),
  scheduler: async () => (await import('./scheduler.js')),
  crawler: async () => (await import('./crawler.js')),
  recognize: async () => (await import('./recognize.js')),
  crack: async () => (await import('./crack.js')),
  auto: async () => (await import('./auto.js')),
  logs: async () => (await import('./logs.js')),
  workflow: async () => (await import('./workflow.js')),
  ai: async () => (await import('./ai.js')),
  xparse: async () => (await import('./xparse.js')),
  anti: async () => (await import('./anti.js')),
  limit: async () => (await import('./limit.js')),
  challenge: async () => (await import('./challenge.js')),
  system: async () => (await import('./system.js')),
  docs: async () => (await import('./docs.js')),
  backend: async () => (await import('./backend.js')),
  train: async () => (await import('./train.js')),
  fastapi: async () => (await import('./fastapi.js')),
  security: async () => (await import('./security.js')),
};

export async function mountModule(name, rootId = 'app-root', options = {}) {
  const loader = MODULES[name];
  if (!loader) throw new Error(`Module not found: ${name}`);
  const mod = await loader();
  const mount = mod?.mount || mod?.default;
  const root = document.getElementById(rootId) || document.body;
  if (typeof mount === 'function') {
    return mount(root, options);
  }
  // 回退：仅动态引入页面脚本
  // 某些旧页面可能在 import 时自执行
  return mod;
}
