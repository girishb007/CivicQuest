'use client';
import {useEffect, useState} from 'react';

export type Viewport = {lat:number; lng:number; zoom:number};
type ExploreState = {center:{lat:number;lng:number};radius:number;filter:string;status:string;list:boolean;search:string;viewport?:Viewport};
const defaults:ExploreState = {center:{lat:19.076,lng:72.878},radius:60000,filter:'all',status:'active',list:false,search:''};
const key='civicquest-explore-v2';
const location=(p:any)=>p&&Number.isFinite(p.lat)&&Number.isFinite(p.lng)&&Math.abs(p.lat)<=90&&Math.abs(p.lng)<=180;

export function useExploreState(){
  const [state,setState]=useState<ExploreState>(defaults);
  const [ready,setReady]=useState(false);
  useEffect(()=>{
    try{
      const saved=JSON.parse(sessionStorage.getItem(key)||'null');
      if(saved&&location(saved.center)&&[3000,60000].includes(saved.radius)
        &&['all','waste','roads','lighting','water','drainage','other'].includes(saved.filter)
        &&['all','active','resolved'].includes(saved.status)&&typeof saved.list==='boolean'
        &&typeof saved.search==='string'&&saved.search.length<=100){
        setState({...defaults,...saved,viewport:location(saved.viewport)&&Number.isFinite(saved.viewport.zoom)
          &&saved.viewport.zoom>=0&&saved.viewport.zoom<=22?saved.viewport:undefined});
      }
    }catch{/* Storage may be unavailable; exploration remains usable. */}
    setReady(true);
  },[]);
  useEffect(()=>{if(ready)try{sessionStorage.setItem(key,JSON.stringify(state));}catch{}},[state,ready]);
  function set<K extends keyof ExploreState>(field:K,value:ExploreState[K]){setState(old=>({...old,[field]:value}));}
  return {state,set,ready};
}
