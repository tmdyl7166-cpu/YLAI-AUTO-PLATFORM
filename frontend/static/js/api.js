// stripped module (to be unified later)
void 0;
export async function apiRun(name, params={}){
	return fetch('/api/run',{
		method:'POST',
		headers:{'Content-Type':'application/json'},
		body:JSON.stringify({name,params})
	}).then(r=>r.json());
}

export async function apiModules(){
	return fetch('/api/modules',{
		method:'GET'
	}).then(r=>r.json());
}

export async function apiStatus(){
	return fetch('/api/status',{
		method:'GET'
	}).then(r=>r.json());
}