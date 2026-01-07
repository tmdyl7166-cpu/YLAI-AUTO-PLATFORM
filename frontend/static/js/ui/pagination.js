// stripped module (to be unified later)
void 0;
// 简易分页控件：事件阻止、页码切换、适配异步加载
export const Pagination = (function(){
  function render(container, { page=1, size=10, total=0, onChange }={}){
    const pages = Math.max(1, Math.ceil((total||0)/(size||10)));
    // clamp page
    page = Math.min(Math.max(1, page), pages);
    container.innerHTML = '';
    const bar = document.createElement('div'); bar.className='yl-page-bar';
    let ticking = false;
    function mk(label, target){ const a=document.createElement('a'); a.href='#'; a.textContent=label; a.addEventListener('click', function(e){ e.preventDefault(); e.stopPropagation(); if(ticking) return; if(target<1||target>pages) return; ticking=true; try{ onChange && onChange(target, size); } finally { setTimeout(()=>{ ticking=false; }, 150); } }); return a; }
    bar.appendChild(mk('«', 1)); bar.appendChild(mk('‹', page-1));
    const info = document.createElement('span'); info.className='yl-page-info'; info.textContent = `${page}/${pages}`; bar.appendChild(info);
    bar.appendChild(mk('›', page+1)); bar.appendChild(mk('»', pages));
    container.appendChild(bar);
  }
  return { render };
})();
