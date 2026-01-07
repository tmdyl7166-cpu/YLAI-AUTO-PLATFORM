// stripped module (to be unified later)
void 0;
// 弹窗管理：层级、嵌套、事件冒泡控制、动画钩子、异步内容
export const Modal = (function(){
  const stack = [];
  const body = typeof document!=='undefined' ? document.body : null;
  function create({ title='提示', content='', onClose=null, asyncLoader=null, disableBackgroundClick=false }={}){
    const overlay = document.createElement('div');
    overlay.className = 'yl-modal-overlay';
    const box = document.createElement('div');
    box.className = 'yl-modal-box';
    const header = document.createElement('div'); header.className='yl-modal-header'; header.textContent=title;
    const close = document.createElement('button'); close.className='yl-modal-close'; close.textContent='×';
    const inner = document.createElement('div'); inner.className='yl-modal-content'; inner.innerHTML = content;
    const footer = document.createElement('div'); footer.className='yl-modal-footer';
    overlay.appendChild(box); box.appendChild(header); box.appendChild(close); box.appendChild(inner); box.appendChild(footer);

    overlay.addEventListener('click', (e)=>{ if(e.target===overlay){ e.stopPropagation(); e.preventDefault(); if(!disableBackgroundClick){ pop(); onClose && onClose({ reason:'background' }); } } });
    box.addEventListener('click', (e)=>{ e.stopPropagation(); });
    close.addEventListener('click', (e)=>{ e.stopPropagation(); e.preventDefault(); pop(); onClose && onClose({ reason:'close' }); });

    if (asyncLoader){
      setTimeout(async()=>{
        try{ const html = await asyncLoader(); if(typeof html==='string'){ inner.innerHTML = html; } }
        catch(_){ /* 忽略失败 */ }
      }, 0);
    }

    return { overlay, box, inner, onClose };
  }
  function push(node){
    if (!body) return;
    const level = stack.length+1;
    node.overlay.style.zIndex = String(1000 + level);
    body.appendChild(node.overlay);
    stack.push(node);
  }
  function pop(){
    const node = stack.pop();
    if (!node || !body) return;
    try{ body.removeChild(node.overlay); }catch(_){}
  }
  function closeAll(){ while(stack.length){ pop(); } }
  return { create, push, pop, closeAll };
})();
