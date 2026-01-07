// Unified topbar renderer: renders consistent navigation and highlights the active page
(function(){
  const header = document.getElementById('topbar');
  if (!header) return;
  if (header.children && header.children.length) return; // respect existing custom render
  const links = [
    { href: '/pages/index.html', label: '首页', key: 'index' },
    { href: '/pages/monitor.html', label: '监控', key: 'monitor' },
    { href: '/pages/run.html', label: '运行', key: 'run' },
    { href: '/pages/api-doc.html', label: 'API文档', key: 'api-doc' },
    { href: '/pages/visual_pipeline.html', label: '可视化', key: 'visual_pipeline' },
    { href: '/pages/ai-demo.html', label: 'AI演示', key: 'ai-demo' },
    { href: '/pages/api-map.html', label: 'API映射', key: 'api-map' },
    { href: '/pages/rbac.html', label: '权限矩阵', key: 'rbac' },
    { href: '/pages/login.html', label: '登录', key: 'login' },
  ];
  function activeKey(){
    const m = location.pathname.match(/\/pages\/(.+?)\.html$/);
    return m ? m[1] : 'index';
  }
  const current = activeKey();
  const nav = document.createElement('nav');
  nav.className = 'topbar';
  links.forEach(({href,label,key})=>{
    const a = document.createElement('a');
    a.href = href; a.textContent = label;
    if (key === current) a.classList.add('active');
    nav.appendChild(a);
  });
  header.innerHTML = '';
  header.appendChild(nav);
})();
