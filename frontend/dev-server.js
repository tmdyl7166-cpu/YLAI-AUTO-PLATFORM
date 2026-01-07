#!/usr/bin/env node
/* Dev server with proxy: /api and /ws -> 127.0.0.1:8001 */
const express = require('express');
const connectLivereload = require('connect-livereload');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');
const app = express();
// Inject livereload script in HTML during development
app.use(connectLivereload({ port: process.env.LIVERELOAD_PORT || 35729 }));
const port = process.env.PORT || 5173;
const ASSET_VERSION = process.env.ASSET_VERSION || new Date().toISOString().slice(0,10).replace(/-/g,'');
const API_HOST = process.env.API_HOST || '127.0.0.1';
const API_PORT = process.env.API_PORT || '8001';
const API_PROTO = process.env.API_PROTO || 'http';
const WS_PROTO = process.env.WS_PROTO || (API_PROTO === 'https' ? 'wss' : 'ws');
const EXTRA_CONNECT = process.env.EXTRA_CONNECT || '';

const root = path.resolve(__dirname);
// 支持无扩展名的页面路由：/pages/name -> /pages/name.html
app.get('/pages/:name', (req, res, next) => {
  const f = (req.params.name||'');
  if (!f.endsWith('.html')) {
    return res.redirect(`/pages/${f}.html`);
  }
  return next();
});
// CSP header to allow local development assets and required connections
app.use((req, res, next) => {
  const connectList = [
    "'self'",
    `${API_PROTO}://${API_HOST}:${API_PORT}`,
    `${WS_PROTO}://${API_HOST}:${API_PORT}`,
  ];
  if (EXTRA_CONNECT) {
    for (const u of EXTRA_CONNECT.split(',').map(s=>s.trim()).filter(Boolean)) {
      connectList.push(u);
    }
  }
  const csp = [
    "default-src 'self'",
    "style-src 'self' 'unsafe-inline' https://www.gstatic.com",
    "style-src-elem 'self' 'unsafe-inline' https://www.gstatic.com",
    "script-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    `connect-src ${connectList.join(' ')}`,
    "font-src 'self' data:",
    "frame-ancestors 'self'",
  ].join('; ');
  res.setHeader('Content-Security-Policy', csp);
  next();
});
app.use('/static', express.static(path.join(root, 'static')));
// HTML 动态注入版本占位符
app.use((req, res, next) => {
  if (!req.path.startsWith('/pages/') || !req.path.endsWith('.html')) return next();
  const rel = req.path.replace(/^\/pages\//, '');
  const fp = path.join(root, 'pages', rel);
  app.set('etag', 'weak');
  res.setHeader('Cache-Control', 'no-cache');
  require('fs').readFile(fp, 'utf8', (err, html) => {
    if (err) return next();
    const fs = require('fs');
    const head = fs.existsSync(path.join(root,'pages/_partials/head.html')) ? fs.readFileSync(path.join(root,'pages/_partials/head.html'),'utf8') : '';
    const footer = fs.existsSync(path.join(root,'pages/_partials/footer.html')) ? fs.readFileSync(path.join(root,'pages/_partials/footer.html'),'utf8') : '';
    const rendered = html
      .replace(/__ASSET_VERSION__/g, ASSET_VERSION)
      .replace(/__HEAD__/g, head)
      .replace(/__FOOTER__/g, footer);
    res.type('html').send(rendered);
  });
});
app.use('/pages', express.static(path.join(root, 'pages')));
app.use('/', express.static(root));
// Redirect root to the main index page to avoid 404 when no root index.html exists
app.get('/', (req, res) => {
  res.redirect('/pages/index.html');
});

app.use('/api', createProxyMiddleware({ target: `${API_PROTO}://${API_HOST}:${API_PORT}`, changeOrigin: true }));
app.use('/ws', createProxyMiddleware({ target: `${WS_PROTO}://${API_HOST}:${API_PORT}`, ws: true }));

app.listen(port, () => {
  console.log(`[dev-server] listening on http://localhost:${port}`);
});
