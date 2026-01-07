// stripped module (to be unified later)
void 0;
// 前端错误与日志同步到后端
// 捕获运行时错误
window.onerror = function (msg, url, line, col, error) {
  try {
    fetch('/api/js-error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source: 'frontend',
        type: 'js_runtime_error',
        file: url,
        line: line,
        message: String(msg || ''),
        stack: (error && error.stack) || ''
      })
    }).catch(()=>{});
  } catch (_) {}
};

// 同步 console.log
(function(){
  try {
    const raw = console.log;
    console.log = function (...args) {
      try {
        fetch('/api/js-console', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source: 'frontend', args })
        }).catch(()=>{});
      } catch(_){}
      return raw.apply(console, args);
    };
  } catch(_){}
})();
