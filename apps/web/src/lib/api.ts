export class ApiError extends Error { constructor(message:string, public code:string, public status:number) { super(message); } }
export function csrf() { return typeof document === 'undefined' ? '' : decodeURIComponent(document.cookie.split('; ').find(c=>c.startsWith('cq_csrf='))?.split('=').slice(1).join('=') || ''); }
let starting:Promise<unknown>|undefined;
export async function ensureSession(){
  if (!csrf()) { starting ||= fetch('/api/v1/sessions/guest',{method:'POST',credentials:'include'}).then(r=>{if(!r.ok)throw new Error('Could not start your guest session');}).finally(()=>{starting=undefined;}); await starting; }
}
export async function api<T=any>(path:string, options:RequestInit={}):Promise<T>{
  await ensureSession();
  const response=await fetch('/api/v1'+path,{...options,credentials:'include',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf(),...(options.headers||{})}});
  const result=await response.json();
  if(!response.ok) throw new ApiError(result.error?.message || 'Please try again.',result.error?.code || 'REQUEST_FAILED',response.status);
  return result;
}
export function post<T=any>(path:string,body:unknown={},key?:string){return api<T>(path,{method:'POST',body:JSON.stringify(body),headers:key?{'Idempotency-Key':key}:{}});}
export type UploadAttempt = {
  authorization?: {id:string;upload_url:string;headers:Record<string,string>};
  uploaded?: boolean;
  completed?: boolean;
};
export async function uploadPhoto(path:string,file:File,role='evidence',attempt:UploadAttempt={}) {
  const type=file.type || (file.name.toLowerCase().endsWith('.heic')?'image/heic':'image/jpeg');
  const signed=attempt.authorization ||= await post(path,{content_type:type,size:file.size,role});
  if(attempt.completed)return signed.id;
  if(!attempt.uploaded){
    const local=signed.upload_url.startsWith('/');
    const response=await fetch(signed.upload_url,{method:'PUT',body:file,credentials:local?'include':'omit',headers:{...signed.headers,...(local?{'X-CSRF-Token':csrf()}:{})}});
    if(!response.ok)throw new Error('Photo upload failed. Please retry.');
    attempt.uploaded=true;
  }
  await post(`/media/${signed.id}/complete`);
  attempt.completed=true;
  return signed.id;
}
export function locate():Promise<{lat:number;lng:number;accuracy_m:number}>{return new Promise((resolve,reject)=>{if(!navigator.geolocation)return reject(new Error('Choose your location manually.'));navigator.geolocation.getCurrentPosition(p=>resolve({lat:p.coords.latitude,lng:p.coords.longitude,accuracy_m:p.coords.accuracy}),()=>reject(new Error('Location is unavailable. You can choose an area manually.')),{enableHighAccuracy:true,timeout:15000,maximumAge:15000});});}
export function pretty(value:string){return value?.replace(/[_-]/g,' ').replace(/\b\w/g,c=>c.toUpperCase()) || '';}
