// stripped module (to be unified later)
void 0;
document.getElementById('runForm').addEventListener('submit', async (e)=>{
	e.preventDefault();
	const name=e.target.name.value;
	let params={};
	try{params=JSON.parse(e.target.params.value||'{}')}catch{}
	const res=await fetch('/api/run',{
		method:'POST',
		headers:{'Content-Type':'application/json'},
		body:JSON.stringify({name,params})
	});
	document.getElementById('result').textContent=await res.text();
});