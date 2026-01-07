export default {
  id: 'module.crack',
  title: '破解任务',
  node: 'node.crack',
  routes: {
    captcha: { method: 'POST', path: '/api/crack/captcha' },
    url: { method: 'POST', path: '/api/crack/url' },
    parse: { method: 'POST', path: '/api/crack/parse' },
    webparse: { method: 'POST', path: '/api/crack/webparse' },
    zip: { method: 'POST', path: '/api/crack/zip' },
    appLogin: { method: 'POST', path: '/api/crack/app-login' },
    defense: { method: 'POST', path: '/api/crack/defense' },
    android: { method: 'POST', path: '/api/crack/android' },
    googlePhotos: { method: 'POST', path: '/api/crack/google-photos' },
    card: { method: 'POST', path: '/api/crack/card' },
    base64: { method: 'POST', path: '/api/crack/base64' },
    denoise: { method: 'POST', path: '/api/crack/denoise' },
    startTask: { method: 'POST', path: '/api/crack/tasks/:id/start' },
    taskStatus: { method: 'GET', path: '/api/crack/tasks/:id/status' },
  },
  actions: {},
  validators: {},
  init(registry) { registry.register(this.id, this); }
};
