// stripped module (to be unified later)
void 0;
// 通用加载动画组件
// 用法：Spinner.show(dom), Spinner.hide(dom)
const Spinner = {
  show: function(dom) {
    if (!dom) return;
    dom.innerHTML = '<div class="spinner"><div></div><div></div><div></div><div></div></div>';
    dom.classList.add('spinner-container');
  },
  hide: function(dom) {
    if (!dom) return;
    dom.innerHTML = '';
    dom.classList.remove('spinner-container');
  }
};
window.Spinner = Spinner;