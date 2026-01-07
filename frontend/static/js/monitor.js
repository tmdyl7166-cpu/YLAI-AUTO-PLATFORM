// stripped module (to be unified later)
void 0;
const log=document.getElementById('log');
async function poll(){
	try{
		const res=await fetch('/api/scripts');
		const data=await res.json();
		log.textContent=`可用脚本: ${data.scripts.join(', ')}`;
	}catch(e){
		log.textContent='无法连接后端';
	}
	setTimeout(poll,3000);
}
poll();