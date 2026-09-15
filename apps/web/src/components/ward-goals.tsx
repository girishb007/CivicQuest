'use client';
import Link from 'next/link';
import {useState} from 'react';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {api,post} from '@/lib/api';

export function WardGoals({areaId,admin=false}:{areaId?:string;admin?:boolean}){
  const cache=useQueryClient();
  const query=useQuery({queryKey:['ward-goals',areaId],queryFn:()=>api('/ward-goals'+(areaId?'?area_id='+areaId:''))});
  const [editing,setEditing]=useState<any>();
  return <section className="form-panel ward-goals"><div className="section-heading"><div><div className="kicker">BETTER TOGETHER</div><h2>Shared ward goals</h2></div>{admin&&<button className="button outline small" onClick={()=>setEditing({})}>Create ward goal</button>}</div>
    <p>Build a shared record of verified outcomes. Your personal XP stays separate.</p>
    {query.isPending?<p role="status">Loading ward goals…</p>:query.isError?<p role="alert">Could not load ward goals. <button onClick={()=>query.refetch()}>Retry</button></p>:<div className="ward-goal-grid">{query.data.items.map((goal:any)=><article className="ward-goal-card" key={goal.id}>
      <Link href={'/areas/'+goal.area_id}>{goal.area_name}</Link><h3>{goal.title}</h3>
      <p>{new Date(goal.starts_at).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})} – {new Date(goal.ends_at).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})} · {goal.status}</p>
      <strong>{goal.progress} / {goal.target} verified outcomes</strong>
      <progress aria-label={goal.title+' progress'} value={Math.min(goal.progress,goal.target)} max={goal.target}/>
      <p>{goal.resolved_reports} waste resolutions · {goal.completed_actions} Civic Actions</p>
      <p className="field-note">{goal.counting_note}</p>{goal.synthetic&&<span className="tag">Illustrative ward</span>}
      {admin&&<button className="button outline small" onClick={()=>setEditing(goal)}>Edit {goal.title}</button>}
    </article>)}</div>}
    {!query.isPending&&!query.isError&&!query.data.items.length&&<p>No shared ward goals have been published yet.</p>}
    {editing&&<GoalEditor initial={editing} onClose={()=>setEditing(undefined)} onSaved={()=>{setEditing(undefined);cache.invalidateQueries({queryKey:['ward-goals']});}}/>}
  </section>;
}

function GoalEditor({initial,onClose,onSaved}:{initial:any;onClose:()=>void;onSaved:()=>void}){
  const geo=useQuery({queryKey:['goal-wards'],queryFn:()=>api('/geography')});
  const [error,setError]=useState('');const [busy,setBusy]=useState(false);
  const [key]=useState(()=>crypto.randomUUID());
  async function submit(e:React.FormEvent<HTMLFormElement>){
    e.preventDefault();setError('');setBusy(true);
    const values=new FormData(e.currentTarget);
    const body={area_id:values.get('area_id'),title:values.get('title'),target:Number(values.get('target')),
      starts_at:new Date(String(values.get('starts_at'))+'T00:00:00+05:30').toISOString(),
      ends_at:new Date(String(values.get('ends_at'))+'T00:00:00+05:30').toISOString(),status:values.get('status')};
    try{if(initial.id)await api('/admin/ward-goals/'+initial.id,{method:'PUT',body:JSON.stringify(body),headers:{'Idempotency-Key':key}});
      else await post('/admin/ward-goals',body,key);onSaved();}catch(e:any){setError(e.message);}finally{setBusy(false);}
  }
  const indianDate=(value?:string)=>value?new Date(value).toLocaleDateString('en-CA',{timeZone:'Asia/Kolkata'}):'';
  return <form className="goal-editor" onSubmit={submit}><h3>{initial.id?'Edit ward goal':'Create ward goal'}</h3>
    <label>Goal title<input name="title" required minLength={3} maxLength={160} defaultValue={initial.title}/></label>
    <label>Administrative ward<select aria-label="Administrative ward" name="area_id" required defaultValue={initial.area_id||''}><option value="" disabled>Select a ward</option>{geo.data?.features.filter((f:any)=>f.properties.type==='ward').map((f:any)=><option key={f.properties.id} value={f.properties.id}>{f.properties.name}</option>)}</select></label>
    <label>Target verified outcomes<input name="target" type="number" required min={1} max={10000} defaultValue={initial.target||5}/></label>
    <label>Start date (Mumbai)<input name="starts_at" type="date" required defaultValue={indianDate(initial.starts_at)}/></label>
    <label>End date, exclusive (Mumbai)<input name="ends_at" type="date" required defaultValue={indianDate(initial.ends_at)}/></label>
    <label>Goal visibility<select aria-label="Goal visibility" name="status" defaultValue={initial.status||'draft'}><option value="draft">Draft</option><option value="published">Published</option><option value="cancelled">Cancelled</option></select></label>
    <p className="field-note">Counts accepted waste resolutions and completed Civic Actions. No extra XP is awarded.</p>
    {error&&<p role="alert" className="error">{error}</p>}
    <div className="button-row"><button className="button dark" disabled={busy||geo.isPending}>Save ward goal</button><button className="button outline" type="button" onClick={onClose}>Close editor</button></div>
  </form>;
}
