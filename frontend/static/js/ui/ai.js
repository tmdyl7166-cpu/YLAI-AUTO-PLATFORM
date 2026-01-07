// stripped module (to be unified later)
void 0;
(function(){
  const API_BASE = window.API_BASE || '';

  window.AI = window.AI || {};

  // Minimal helper: send terminal error to /ai/optimize
  window.AI.optimizeError = async function(errorText, context){
    try {
      const res = await fetch(`${API_BASE}/ai/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error_text: errorText, context: context || {} })
      });
      const data = await res.json();
      return data;
    } catch (err) {
      return { code: 1, error: String(err) };
    }
  };
})();
