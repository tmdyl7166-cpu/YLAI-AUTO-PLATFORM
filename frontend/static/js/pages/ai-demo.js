// stripped page controller
void 0;
// AI Demo Page - single entry module
// Prefer unified module mounting; fallback to local implementation when module missing
(async ()=>{ try { const { mountModule } = await import('../modules/registry.js?v=__ASSET_VERSION__'); const ok = await mountModule('ai-demo'); if (ok) return; } catch (_) { /* fallback to local below */ } })();
// Minimal clickable module placeholder guard
(function ensureMinimal(){
  const root = document.getElementById('ai-demo-root');
  if (root && !root.children.length) {
    const section = document.createElement('section');
    section.className = 'card';
    const btn = document.createElement('button');
    btn.className = 'btn';
    btn.textContent = '打开 AI 调度';
    btn.onclick = ()=> alert('AI 调度占位（后续由模块渲染）');
    section.appendChild(btn);
    root.appendChild(section);
  }
})();
// Renders UI, binds events, calls backend /api/generate

import { showToast } from '/static/js/components/toast.js';

function byId(id){ return document.getElementById(id); }
function safeAppend(parent, child){ if(parent && child) parent.appendChild(child); }

async function getAuthHeaders(){
  try {
    const mod = await import('/static/js/auth.js');
    return mod.auth?.getAuthHeaders?.() || {};
  } catch (_) { return {}; }
}

function createTopbar(){
  // 顶栏由 common/topbar.js 统一渲染，仅确保占位容器存在
  const el = document.getElementById('topbar');
  if(!el){ const h=document.createElement('header'); h.id='topbar'; document.body.prepend(h); }
}

function renderForm(root){
  const wrap = document.createElement('div');
  wrap.className = 'yl-card yl-container';
  wrap.innerHTML = `
    <h1 class="title">AI模型推理演示</h1>
    <div class="form-grid">
      <label>选择模型
        <select id="model">
          <option value="deepseek-r1-8b">deepseek-r1-8b</option>
          <option value="qwen3-coder:480b-cloud">qwen3-coder:480b-cloud</option>
          <option value="qwen3-vl:235b-instruct-cloud">qwen3-vl:235b-instruct-cloud</option>
          <option value="deepseek-v3.1:671b-cloud">deepseek-v3.1:671b-cloud</option>
        </select>
      </label>
      <label>temperature
        <input type="number" id="temperature" min="0" max="2" step="0.01" value="0.7" />
      </label>
      <label>max_tokens
        <input type="number" id="max_tokens" min="1" max="4096" step="1" value="512" />
      </label>
      <label>输入 Prompt
        <textarea id="prompt" placeholder="请输入推理内容..."></textarea>
      </label>
      <div class="btn-row">
        <button id="runBtn" class="primary">调用 /generate 推理</button>
      </div>
      <div class="result" id="result"></div>
      <div class="actions">
        <button id="trainBtn" class="ghost">AI训练（占位）</button>
        <button id="deployBtn" class="ghost">学习部署（占位）</button>
        <button id="linkBtn" class="ghost">功能联动（占位）</button>
      </div>
    </div>`;
  safeAppend(root, wrap);
}

function getApiBase(){ return location.origin; }

async function runGenerate(){
  const runBtn = byId('runBtn');
  const resultEl = byId('result');
  if(!runBtn || !resultEl) return;
  const model = byId('model')?.value || 'deepseek-r1-8b';
  const temperature = parseFloat(byId('temperature')?.value || '0.7');
  const max_tokens = parseInt(byId('max_tokens')?.value || '512');
  const prompt = byId('prompt')?.value || '';

  runBtn.disabled = true; runBtn.textContent = '推理中...';
  resultEl.textContent = '推理中...';
  try {
    const headers = Object.assign({ 'Content-Type': 'application/json' }, await getAuthHeaders());
    const resp = await fetch(getApiBase() + '/api/generate', {
      method: 'POST', headers, body: JSON.stringify({ model, temperature, max_tokens, prompt })
    });
    const data = await resp.json();
    resultEl.textContent = data.result || data.response || JSON.stringify(data, null, 2);
    showToast('推理完成','success');
  } catch (e) {
    resultEl.textContent = '推理失败：' + e;
    showToast('推理失败','error');
  } finally {
    runBtn.disabled = false; runBtn.textContent = '调用 /generate 推理';
  }
}

function bindEvents(){
  byId('runBtn')?.addEventListener('click', runGenerate);
  byId('trainBtn')?.addEventListener('click', ()=> showToast('AI训练功能占位，后续扩展','info'));
  byId('deployBtn')?.addEventListener('click', ()=> showToast('学习部署功能占位，后续扩展','info'));
  byId('linkBtn')?.addEventListener('click', ()=> showToast('功能联动入口占位，后续扩展','info'));
}

function reveal(){
  const root = byId('ai-demo-root');
  if(root) root.style.opacity = '1';
}

function ensureRoot(){
  if(!document.getElementById('topbar')){
    const h = document.createElement('header'); h.id = 'topbar'; document.body.prepend(h);
  }
  if(!document.getElementById('ai-demo-root')){
    const m = document.createElement('main'); m.id = 'ai-demo-root'; document.body.appendChild(m);
  }
}

function setup(){
  ensureRoot();
  createTopbar();
  const root = document.getElementById('ai-demo-root');
  if(!root) return;
  renderForm(root);
  bindEvents();
  reveal();
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', setup);
}else{ setup(); }
