// stripped page controller
void 0;
// 简易事件总线（监控页）
(function(){
  const target = new EventTarget();
  window.MON_BUS = {
    on: (type, fn)=> target.addEventListener(type, fn),
    off: (type, fn)=> target.removeEventListener(type, fn),
    emit: (type, detail)=> target.dispatchEvent(new CustomEvent(type, { detail }))
  };
})();
