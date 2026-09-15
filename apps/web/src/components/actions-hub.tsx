'use client';

import {useQuery} from '@tanstack/react-query';
import {ArrowRight,Check,Flag,MapPin,ShieldCheck,Trophy,Users} from 'lucide-react';
import Link from 'next/link';
import {useState} from 'react';

import {api,post} from '@/lib/api';
import {WardGoals} from './ward-goals';

type Props={me:any;busy:boolean;act:(fn:()=>Promise<any>,message?:string)=>Promise<any>};

export function ActionsHub({me,busy,act}:Props){
 const [tab,setTab]=useState('quests');const quests=useQuery({queryKey:['quests'],queryFn:()=>api('/quests')});const actions=useQuery({queryKey:['actions'],queryFn:()=>api('/civic-actions')});const groups=useQuery({queryKey:['community-groups'],queryFn:()=>api('/community-groups')});const reports=useQuery({queryKey:['my-reports'],queryFn:()=>api('/me/reports')});
 return <><header className="page-title"><span className="kicker">ACTIONS · QUEST LOG</span><h1>Choose your next contribution</h1><p>Personal progress and shared ward outcomes use the same verified civic records.</p></header><div className="hub-tabs" role="tablist">{[['quests','Missions'],['actions','Actions'],['reports','My reports'],['groups','Groups']].map(([value,label])=><button role="tab" aria-selected={tab===value} className={tab===value?'selected':''} onClick={()=>setTab(value)} key={value}>{label}</button>)}</div>
 {tab==='quests'&&<><div className="mobile-quest-list">{quests.data?.items?.map((quest:any)=><article key={quest.code}><Flag/><div><span className="kicker">{quest.period}</span><h2>{quest.title}</h2><p>{quest.description}</p><progress max={quest.target} value={quest.progress}/><small>{quest.progress} of {quest.target}</small></div><button disabled={busy||!quest.claimable} onClick={()=>act(()=>post(`/quests/${quest.code}/claim`),'Quest reward recorded')}>{quest.completed?<Check/>:quest.claimable?`+${quest.xp}`:<ArrowRight/>}</button></article>)}</div><WardGoals/><Link className="hub-link" href="/leaderboard"><Trophy/>Ward leaderboard<ArrowRight/></Link></>}
 {tab==='actions'&&<div className="mobile-action-list">{actions.data?.items?.map((item:any)=><Link href={`/actions/${item.id}`} key={item.id}><span className="action-icon"><Users/></span><div><span className="kicker">CIVIC ACTION</span><h2>{item.title}</h2><p><MapPin size={13}/>{item.location_name}</p></div><ArrowRight/></Link>)}</div>}
 {tab==='reports'&&<div className="mobile-action-list">{reports.data?.items?.map((item:any)=><Link href={`/i/${item.public_code}`} key={item.id}><span className={`severity-pill ${item.severity}`}>{item.severity}</span><div><span className="kicker">{item.public_code}</span><h2>{item.title}</h2><p>{item.status} · {item.verification}</p></div><ArrowRight/></Link>)}{!reports.data?.items?.length&&<div className="state"><Flag/><p>Your submitted reports will appear here.</p></div>}</div>}
 {tab==='groups'&&<><p className="hub-explainer"><ShieldCheck/>Groups are reviewed directory records with external contact links. CivicQuest does not manage membership.</p><div className="mobile-action-list">{groups.data?.items?.map((item:any)=><article key={item.id}><span className="action-icon"><Users/></span><div><span className="kicker">{item.coverage}</span><h2>{item.name}</h2><p>{item.description}</p><small>Source checked {new Date(item.provenance.verified_at).toLocaleDateString('en-IN')}{item.provenance.review_due?' · review due':''}</small></div><a className="button outline" href={item.contact_url} target="_blank" rel="noreferrer">Contact</a></article>)}</div></>}
 </>
}
