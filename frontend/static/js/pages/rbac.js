// minimal rbac page entry: ensure containers and placeholder only
void 0;
(function(){
	function ensureContainers(){
		if(!document.getElementById('topbar')){ const h=document.createElement('header'); h.id='topbar'; document.body.prepend(h); }
		if(!document.getElementById('rbac-root')){ const m=document.createElement('main'); m.id='rbac-root'; document.body.appendChild(m); }
	}
	function renderPlaceholder(){
		const root=document.getElementById('rbac-root'); if(!root) return;
		if(!root.children.length){
			const section=document.createElement('section'); section.className='card';
			const btn=document.createElement('button'); btn.className='btn'; btn.textContent='打开权限矩阵';
			btn.onclick=()=> alert('权限矩阵占位（后续由模块渲染）');
			section.appendChild(btn);
			root.appendChild(section);
		}
	}
	function init(){ ensureContainers(); renderPlaceholder(); const root=document.getElementById('rbac-root'); if(root) root.style.opacity='1'; }
	if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', init); } else { init(); }
})();
