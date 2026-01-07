// stripped module (to be unified later)
void 0;
// 通用进度条组件
// 用法：ProgressBar.attach(dom, { percent: 0, color: '#42e695', text: '0%' })
const ProgressBar = {
  attach: function(dom, opts={}) {
    if (!dom) return;
    dom.classList.add('progress-bar-container');
    dom.innerHTML = `
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" style="width:${opts.percent||0}%;background:${opts.color||'#42e695'}"></div>
      </div>
      <span class="progress-bar-text">${opts.text||''}</span>
    `;
  },
  update: function(dom, percent, text) {
    if (!dom) return;
    const fill = dom.querySelector('.progress-bar-fill');
    const txt = dom.querySelector('.progress-bar-text');
    if (fill) fill.style.width = percent + '%';
    if (txt) txt.textContent = text || (percent + '%');
  }
};
window.ProgressBar = ProgressBar;