// stripped module (to be unified later)
void 0;
(function(){
  function injectGeneratedNav(){
    var nav = document.querySelector('.header .nav');
    if(!nav) return;
    var li = document.createElement('li');
    var a = document.createElement('a');
    a.href = '/pages/generated/index.html';
    a.textContent = '自动生成模块';
    li.appendChild(a);
    // 插入到前三个菜单之后
    if (nav.children && nav.children.length >= 3) {
      nav.insertBefore(li, nav.children[3]);
    } else {
      nav.appendChild(li);
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectGeneratedNav);
  } else {
    injectGeneratedNav();
  }
})();
