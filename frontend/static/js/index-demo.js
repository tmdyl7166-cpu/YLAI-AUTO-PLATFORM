// stripped module (to be unified later)
void 0;
// 首页演示：弹窗嵌套、分页与风控接口占位
import { Modal } from './ui/modal.js';
import { Pagination } from './ui/pagination.js';
import { Http } from './utils/http.js';

function bindModalDemo(){
  const openBtn = document.getElementById('btn-open-modal');
  const nestedBtn = document.getElementById('btn-open-nested');
  if(openBtn){
    openBtn.addEventListener('click', (e)=>{
      e.preventDefault(); e.stopPropagation();
      const node = Modal.create({ title: '一级弹窗', content: '<div>这是一级弹窗内容。</div>', onClose:(res)=>{ console.log('一级弹窗关闭', res); } });
      Modal.push(node);
      node.box.focus && node.box.focus();
    });
  }
  if(nestedBtn){
    nestedBtn.addEventListener('click', (e)=>{
      e.preventDefault(); e.stopPropagation();
      const node1 = Modal.create({ title: '一级弹窗', content: '<div>父弹窗，包含一个打开子弹窗的按钮。</div><div class="btn-row"><button class="btn" id="open-child">打开子弹窗</button></div>', onClose:(res)=>{ console.log('父弹窗关闭', res); } });
      Modal.push(node1);
      node1.box.querySelector('#open-child')?.addEventListener('click', (ev)=>{
        ev.preventDefault(); ev.stopPropagation();
        const node2 = Modal.create({ title: '二级弹窗', content: '<div>这是嵌套的二级弹窗。</div>', disableBackgroundClick:true, onClose:(res)=>{ console.log('子弹窗关闭', res); node1.box.focus && node1.box.focus(); } });
        Modal.push(node2);
        node2.box.focus && node2.box.focus();
      });
    });
  }
}

function bindPaginationDemo(){
  const cont = document.getElementById('demo-page-container');
  if(!cont) return;
  const mock = Array.from({length: 37}).map((_,i)=>`Item ${i+1}`);
  function renderPage(page, size){
    const start=(page-1)*size; const items=mock.slice(start,start+size);
    cont.innerHTML='';
    const list=document.createElement('ul'); list.className='list';
    items.forEach(t=>{ const li=document.createElement('li'); li.textContent=t; list.appendChild(li); });
    cont.appendChild(list);
    const pager=document.createElement('div');
    Pagination.render(pager,{page,size,total:mock.length,onChange:renderPage});
    cont.appendChild(pager);
  }
  renderPage(1,10);
}

function bindRiskDemo(){
  const btnProgress=document.getElementById('btn-risk-progress');
  const btnCaptcha=document.getElementById('btn-captcha-demo');
  const out=document.getElementById('risk-out');
  if(btnProgress){ btnProgress.addEventListener('click', async (e)=>{ e.preventDefault(); e.stopPropagation(); const res=await Http.request('/api/auto/risk/progress'); out && (out.textContent=JSON.stringify(res.data,null,2)); }); }
  if(btnCaptcha){ btnCaptcha.addEventListener('click', async (e)=>{ e.preventDefault(); e.stopPropagation(); const fd=new FormData(); fd.append('image', new Blob(['demo'],{type:'application/octet-stream'}), 'demo.bin'); const res=await Http.request('/api/crack/captcha',{method:'POST', body: fd}); out && (out.textContent=JSON.stringify(res.data,null,2)); }); }
}

function init(){ bindModalDemo(); bindPaginationDemo(); bindRiskDemo(); }

if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', init); } else { init(); }
