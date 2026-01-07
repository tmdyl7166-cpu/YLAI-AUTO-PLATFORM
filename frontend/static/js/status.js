// stripped module (to be unified later)
void 0;
// 统一拉取并渲染项目状态文档（markdown 原文或简单转换）
(function(){
  async function fetchStatus(){
    try{
      const res = await fetch('/api/status');
      const data = await res.json();
      if(data.code !== 0) throw new Error(data.error || 'status error');
      return data.data.markdown || '';
    }catch(e){
      return `加载失败: ${String(e)}`;
    }
  }
  function renderMarkdown(md){
    // 简易渲染：保留标题与列表，其他按文本展示，避免引入外部库
    const lines = md.split(/\r?\n/);
    const html = lines.map(l=>{
      if(l.startsWith('# ')) return `<h1>${escapeHtml(l.slice(2))}</h1>`;
      if(l.startsWith('## ')) return `<h2>${escapeHtml(l.slice(3))}</h2>`;
      if(l.startsWith('### ')) return `<h3>${escapeHtml(l.slice(4))}</h3>`;
      if(l.startsWith('- ')) return `<li>${escapeHtml(l.slice(2))}</li>`;
      if(l.match(/^\d+\. /)) return `<li>${escapeHtml(l.replace(/^\d+\. /,''))}</li>`;
      if(l.trim()==='') return '';
      return `<p>${escapeHtml(l)}</p>`;
    }).join('\n');
    // 包装列表为 ul
    const fixed = html.replace(/(<li>[^<]*<\/li>\n?)+/g, m=>`<ul>${m}</ul>`);
    return fixed;
  }
  function escapeHtml(s){
    return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
  }
  async function mount(containerId){
    const el = document.getElementById(containerId || 'project-status');
    if(!el) return;
    el.innerHTML = '<div class="loading">加载任务进度...</div>';
    const md = await fetchStatus();
    el.innerHTML = renderMarkdown(md);
  }
  // 自动渲染（页面含有 #project-status 时）
  document.addEventListener('DOMContentLoaded', ()=>{
    const el = document.getElementById('project-status');
    if(el) mount('project-status');
  });
  window.ProjectStatus = { mount };
})();
