// stripped module (to be unified later)
void 0;
// 首页模块列表渲染：依赖 modules.js，零内联
import { apiModules, bindQuickActions, renderModulesPaged } from './modules.js';

async function init(){
  try{
    const list = await apiModules();
    const box = document.getElementById('modules-list');
    if(!box) return;
    renderModulesPaged(box, list, { page: 1, size: 12 });
    bindQuickActions(box);
  }catch(e){ /* 静默，不阻塞首页 */ }
}

if (document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
