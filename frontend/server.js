const express = require('express');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');

const PORT = process.env.PORT || 8080;
const ASSET_VERSION = process.env.ASSET_VERSION || process.env.npm_package_version || 'dev';
// 后端目标参数化，兼容旧变量 API_TARGET
const API_PROTO = process.env.API_PROTO || 'http';
const API_HOST = process.env.API_HOST || '127.0.0.1';
const API_PORT = process.env.API_PORT || '8001';
const API_TARGET = process.env.API_TARGET || `${API_PROTO}://${API_HOST}:${API_PORT}`;

const app = express();

// Static assets: serve frontend pages and static resources
const pagesDir = path.join(__dirname, 'pages');
const staticDir = path.join(__dirname, 'static');
// 支持无扩展名的页面路由：/pages/name -> /pages/name.html
app.get('/pages/:name', (req, res, next) => {
  const f = req.params.name || '';
  if (!f.endsWith('.html')) {
    return res.redirect(`/pages/${f}.html`);
  }
  return next();
});
// HTML 动态注入版本占位符
app.get('/pages/:file', (req, res, next) => {
  const fp = path.join(pagesDir, req.params.file);
  if (!fp.endsWith('.html')) return next();
  res.setHeader('Cache-Control', 'no-cache');
  require('fs').readFile(fp, 'utf8', (err, html) => {
    if (err) return next();
    const fs = require('fs');
    const head = fs.existsSync(path.join(pagesDir,'_partials/head.html')) ? fs.readFileSync(path.join(pagesDir,'_partials/head.html'),'utf8') : '';
    const footer = fs.existsSync(path.join(pagesDir,'_partials/footer.html')) ? fs.readFileSync(path.join(pagesDir,'_partials/footer.html'),'utf8') : '';
    const rendered = html
      .replace(/__ASSET_VERSION__/g, ASSET_VERSION)
      .replace(/__HEAD__/g, head)
      .replace(/__FOOTER__/g, footer);
    res.type('html').send(rendered);
  });
});
app.use('/pages', express.static(pagesDir, { fallthrough: true }));
app.use('/static', express.static(staticDir, { fallthrough: true }));

// Root redirect to index
app.get('/', (req, res) => {
  res.redirect('/pages/index.html');
});

// API proxy to backend (supports WebSocket)
app.use('/api', createProxyMiddleware({
  target: API_TARGET,
  changeOrigin: true,
  ws: true,
  logLevel: 'warn',
}));

// WebSocket namespaces proxy (if backend exposes /ws)
app.use('/ws', createProxyMiddleware({
  target: API_TARGET,
  changeOrigin: true,
  ws: true,
  logLevel: 'warn',
}));

// Health endpoint for local dev server
app.get('/health', (req, res) => {
  res.json({ ok: true, ts: Date.now(), apiTarget: API_TARGET, proto: API_PROTO, host: API_HOST, port: API_PORT });
});

app.listen(PORT, () => {
  console.log(`[frontend] listening on http://127.0.0.1:${PORT} -> API ${API_TARGET}`);
});
