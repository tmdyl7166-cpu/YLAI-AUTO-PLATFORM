// stripped module (to be unified later)
void 0;
// 模块列表与快捷操作：统一事件管理、阻止冒泡、分页与懒加载适配
import { Http } from './utils/http.js';
import { Modal } from './ui/modal.js';
import { Pagination } from './ui/pagination.js';

// 统一获取鉴权头（前端自动附加），避免 401
async function getAuthHeaders(){
  try{
    const mod = await import('/static/js/auth.js');
    return mod.auth.getAuthHeaders?.() || {};
  }catch(_){ return {}; }
}

export function renderModulesPaged(container, list, { page=1, size=12 }={}){
  const start = (page-1)*size;
  const items = list.slice(start, start+size);
  container.innerHTML = '';
  const grid = document.createElement('div'); grid.className='module-grid';
  items.forEach(name => {
    const card = document.createElement('div');
    card.className = 'module-card';
    card.innerHTML = `<h4>${name}</h4><ul><li>脚本：${name}.py</li><li>接口：/api/${name}</li></ul><div class="btn-row" style="margin-top:8px"><button class="btn" data-act="run" data-name="${name}">运行</button><button class="btn" data-act="status">状态</button><button class="btn" data-act="curl" data-name="${name}">调用</button></div>`;
    grid.appendChild(card);
  });
  container.appendChild(grid);
  const pager = document.createElement('div');
  Pagination.render(pager, { page, size, total: list.length, onChange: (p,s)=>renderModulesPaged(container, list, { page:p, size:s }) });
  container.appendChild(pager);
}

export function escapeHtml(str){
  return String(str).replace(/[&<>"']/g, s=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[s]));
}
// Shared module helpers for unified backend modules
// Provides apiModules(), apiStatus(), and bindQuickActions(container)

export async function apiModules(){
  try{
    const authH = await getAuthHeaders();
    // 优先调用统一端点 /scripts（公开，无鉴权也尝试）
    const r1 = await fetch('/scripts', { headers: { ...authH } });
    if(r1.ok){
      const j1 = await r1.json();
      if(j1 && j1.code === 0 && Array.isArray(j1.data)) return j1.data;
    }
    // 回退到旧端点 /api/modules（通常需要鉴权）
    const r2 = await fetch('/api/modules', { headers: { ...authH } });
    if(r2.ok){
      const j2 = await r2.json();
      if(j2 && Array.isArray(j2.data)) return j2.data;
    }
    return [];
  }catch(e){ return []; }
}

export async function apiStatus(){
  try{
    const authH = await getAuthHeaders();
    const r = await fetch('/api/status', { headers: { ...authH } });
    return await r.json();
  }catch(e){ return { code:1, error:String(e) }; }
}

export function bindQuickActions(container){
  if(!container) return;
  // 委托绑定，支持分页后 DOM 变化
  container.addEventListener('click', async function(e){
    const btn = e.target.closest('[data-act]');
    if(!btn || !container.contains(btn)) return;
    e.preventDefault();
    e.stopPropagation();
    const act = btn.dataset.act;
    const name = btn.dataset.name;
    try{
      if(act === 'run' && name){
        const url = `/pages/run.html?script=${encodeURIComponent(name)}`;
        publishInvoke('NAV', url, 'modules:quick-action');
        window.location.href = url;
      }else if(act === 'status'){
        const url = '/api/status';
        const j = await apiStatus();
        publishInvoke('GET', url, 'modules:quick-action');
        if((localStorage.getItem('yl_dbg_snapshot') ?? 'true') === 'true'){
          try{ const authH = await getAuthHeaders(); await fetch('/api/snapshot',{method:'POST', headers:{'Content-Type':'application/json', ...authH}, body: JSON.stringify({ kind:'api', action:'status', response:j, script_version: (window.__APP_VER__||'') })}); }catch(_){ }
        }
        alert('状态: '+JSON.stringify(j));
      }else if(act === 'curl' && name){
        const url = `/api/${name}`;
        const authH = await getAuthHeaders();
        const r = await fetch(url, { headers: { ...authH } });
        const t = await r.text();
        publishInvoke('GET', url, 'modules:quick-action');
        if((localStorage.getItem('yl_dbg_snapshot') ?? 'true') === 'true'){
          try{ await fetch('/api/snapshot',{method:'POST', headers:{'Content-Type':'application/json', ...authH}, body: JSON.stringify({ kind:'api', action:'curl', url, response:t, script_version: (window.__APP_VER__||'') })}); }catch(_){ }
        }
        alert(`GET /api/${name} -> `+t);
      }
    }catch(err){ alert('操作失败: '+err); }
  });
}

// 统一事件发布与版本打印，便于上下文联动与冒泡检测
export function publishInvoke(method, url, source){
  try{
    const payload = { ts: Date.now(), method, url, source: source||'modules' };
    if(window.UIBus && typeof window.UIBus.publish === 'function'){
      window.UIBus.publish('api:invoke', payload);
    }
    const detail = { detail: payload };
    window.dispatchEvent(new CustomEvent('modules:invoke', detail));
    // 可选：将冒泡信息通过 WebSocket 回传后端，便于集中记录与UI红点
    const wsBubble = (localStorage.getItem('yl_dbg_wsBubble') ?? 'true') === 'true';
    if(wsBubble){
      try{
        const proto = (window.location.protocol==='https:')?'wss://':'ws://';
        const ws = new WebSocket(proto + window.location.host + '/ws/logs');
        ws.onopen = function(){ try{ ws.send(JSON.stringify({ type:'invoke', ...payload })); }catch(_){} };
        ws.onmessage = function(){ try{ ws.close(); }catch(_){} };
      }catch(_){ /* ignore */ }
    }
  }catch{ /* ignore */ }
}

export function printVersion(){
  try{
    const ver = 'modules.js v1.0';
    console.info('[modules]', ver);
  }catch{ /* ignore */ }
}

// 辅助：根据当前页面路径解析相对/绝对资源前缀
export function resolve(path){
  try{
    if(!path) return '';
    if(path.startsWith('http://') || path.startsWith('https://')) return path;
    // 优先使用根相对，避免层级影响
    if(path.startsWith('/')) return path;
    // 针对特殊部署（如 pages 子目录），自动拼接到根
    const base = location.pathname.startsWith('/pages/') ? '/' : '';
    return base + path.replace(/^\.\//,'');
  }catch{ return path; }
}
