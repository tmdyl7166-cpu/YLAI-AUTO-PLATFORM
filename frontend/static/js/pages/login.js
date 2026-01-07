// minimal login page entry: ensure containers and placeholder only
void 0;
(function(){
	function ensureContainers(){
		if(!document.getElementById('topbar')){ const h=document.createElement('header'); h.id='topbar'; document.body.prepend(h); }
		if(!document.getElementById('login-root')){ const m=document.createElement('main'); m.id='login-root'; document.body.appendChild(m); }
	}
	function renderPlaceholder(){
		const root=document.getElementById('login-root'); if(!root) return;
		if(!root.children.length){
			const section=document.createElement('section'); section.className='card';
			const btn=document.createElement('button'); btn.className='btn'; btn.textContent='登录占位';
			btn.onclick=()=> alert('登录占位（后续由模块渲染）');
			section.appendChild(btn);
			root.appendChild(section);
		}
	}
	function bindLightEvents(){
		// 轻量事件：示例提示，不涉及业务逻辑
		document.addEventListener('keydown', (e)=>{
			if(e.key==='Enter' && (e.target && e.target.tagName==='INPUT')){
				// 仅提示示意
				console.log('[login] Enter pressed');
			}
		});
	}
	function init(){ ensureContainers(); renderPlaceholder(); bindLightEvents(); const root=document.getElementById('login-root'); if(root) root.style.opacity='1'; }
	if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', init); } else { init(); }
})();
