const express = require('express');
const bodyParser = require('body-parser');
const app = express();
const PORT = process.env.PORT || process.env.API_PORT || 8001;

app.use(bodyParser.json());

app.get('/health', (req, res) => {
  res.json({ ok: true, ts: Date.now(), service: 'backend-mock', port: PORT });
});

app.post('/api/run', (req, res) => {
  const payload = req.body || {};
  res.json({ ok: true, echo: payload, ts: Date.now() });
});

app.get('/api/modules', (req, res) => {
  res.json(['demo', 'status', 'log']);
});

// Simple status endpoint for monitor page
app.get('/api/status', (req, res) => {
  res.json({ ok: true, uptime: process.uptime(), modules: ['policy','scheduler','logs'], ts: Date.now() });
});

// Server-Sent Events mock logs stream
app.get('/api/sse/logs', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders && res.flushHeaders();
  let i = 0;
  const interval = setInterval(() => {
    const payload = { lines: [
      `[${new Date().toLocaleTimeString()}] mock log line ${i}`,
      i % 3 === 0 ? { type: 'AI_OPTIMIZE', result: { data: { summary: '示例建议', fixes: [{ title: '修复提示', steps: ['检查接口','添加鉴权','重试'] }] } }, error_text: 'mock error' } : undefined
    ].filter(Boolean) };
    res.write(`data: ${JSON.stringify(payload)}\n\n`);
    i++;
  }, 2000);
  req.on('close', () => { clearInterval(interval); });
});

app.listen(PORT, () => {
  console.log(`[backend-mock] listening on http://127.0.0.1:${PORT}`);
});
