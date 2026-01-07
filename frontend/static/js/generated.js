// stripped module (to be unified later)
void 0;
(function(){
  function qs(sel, root){ return (root||document).querySelector(sel); }
  function qsa(sel, root){ return Array.prototype.slice.call((root||document).querySelectorAll(sel)); }
  function toJSONSafe(x){ try{ return JSON.stringify(x,null,2); }catch(_){ return String(x); } }

  async function callApi(method, path, body, isForm){
    const opts = { method: method || 'GET', headers: {} };
    if (method === 'POST'){
      if (isForm){
        opts.body = body || new FormData();
      } else {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body||{});
      }
    }
    const res = await fetch(path, opts);
    let data;
    try{ data = await res.json(); }catch(_){ data = await res.text(); }
    return data;
  }

  function collectInputs(fnEl){
    const inputs = qsa('input[data-input], textarea[data-input], select[data-input]', fnEl);
    const hasFile = !!qs('input[type="file"][data-input]', fnEl);
    if (hasFile){
      const fd = new FormData();
      inputs.forEach(i => {
        const key = i.getAttribute('data-input');
        if (i.type === 'file'){
          if (i.files && i.files.length>0){ fd.append(key, i.files[0]); }
        } else {
          fd.append(key, i.value);
        }
      });
      return { data: fd, isForm: true };
    } else {
      const payload = {};
      inputs.forEach(i => { payload[i.getAttribute('data-input')] = i.value; });
      return { data: payload, isForm: false };
    }
  }

  function bindFnCard(fnEl){
    const btn = qs('.call-btn', fnEl);
    if(!btn) return;
    const method = (btn.getAttribute('data-method')||'GET').toUpperCase();
    const path = btn.getAttribute('data-path');
    const out = qs('.out', fnEl);
    const encode = (fnEl.getAttribute('data-encode')||'').toLowerCase();
    btn.addEventListener('click', async function(){
      try{
        let body, isForm = false;
        if (method === 'POST'){
          const collected = collectInputs(fnEl);
          body = collected.data;
          isForm = collected.isForm || encode === 'multipart';
        }
        const data = await callApi(method, path, body, isForm);
        if(out) out.textContent = toJSONSafe(data);
      }catch(e){ if(out) out.textContent = String(e); }
    });
  }

  function init(){
    qsa('.fn').forEach(bindFnCard);
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
