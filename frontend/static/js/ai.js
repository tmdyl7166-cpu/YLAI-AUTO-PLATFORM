// stripped module (to be unified later)
void 0;
// 简易封装：调用后端 /ai/pipeline
(function() {
  async function runAIPipeline(prompt, extraParams) {
    try {
      const res = await fetch('/ai/pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.assign({ prompt }, extraParams || {}))
      });
      const data = await res.json();
      // 后端返回 {code, result}
      return data.result || data.data || data;
    } catch (e) {
      return { error: String(e) };
    }
  }

  async function optimizeError(text, meta){
    try{
      const res = await fetch('/ai/optimize',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ text, meta: meta||{} })
      });
      return await res.json();
    }catch(e){ return { code:1, error:String(e) }; }
  }

  // 绑定按钮入口（若页面存在以下元素）
  function bindUI() {
    const btn = document.getElementById('ai-run-btn');
    const input = document.getElementById('ai-prompt-input');
    const out = document.getElementById('ai-result');
    if (!btn || !input) return;
    btn.addEventListener('click', async () => {
      const prompt = (input.value || '').trim();
      if (!prompt) return;
      btn.disabled = true; btn.innerText = '运行中...';
      const result = await runAIPipeline(prompt);
      btn.disabled = false; btn.innerText = '运行 AI';
      if (out) {
        if (typeof result === 'object') {
          out.textContent = JSON.stringify(result, null, 2);
        } else {
          out.textContent = String(result);
        }
      } else {
        console.log('[AI结果]', result);
      }
    });
  }

  // 对外暴露
  window.AIHelper = { runAIPipeline, optimizeError, bindUI };
  // 自动绑定（页面加载完成）
  document.addEventListener('DOMContentLoaded', bindUI);
})();
