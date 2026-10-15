let token='';
export async function api(path:string,body?:unknown){
 if(body!==undefined&&!token){const r=await fetch('/api/session');token=(await r.json()).owner_token;}
 const r=await fetch('/api'+path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json','X-Owner-Token':token},body:body===undefined?undefined:JSON.stringify(body)});
 if(!r.ok){if(r.status===403)token='';let d;try{d=await r.json()}catch{d={detail:r.statusText}}throw new Error(typeof d.detail==='string'?d.detail:JSON.stringify(d.detail));}
 return r.json();
}
