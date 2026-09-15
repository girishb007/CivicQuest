'use client';
import {useEffect,useRef,useState} from 'react';
import maplibregl,{Map as MapInstance,GeoJSONSource} from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type {Viewport} from '@/lib/explore-state';

type Location={lat:number;lng:number};
export type ReportMarker={id:string;title:string;category:string;status:string;severity?:string;lat:number;lng:number};
const points=(items:ReportMarker[])=>({type:'FeatureCollection' as const,features:items.map(item=>({type:'Feature' as const,geometry:{type:'Point' as const,coordinates:[item.lng,item.lat]},properties:{id:item.id,title:item.title,category:item.category,status:item.status,severity:item.severity||'medium'}}))});
const localBaseStyle:any={version:8,sources:{'openstreetmap':{type:'raster',tiles:['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],tileSize:256,attribution:'© OpenStreetMap contributors'}},layers:[{id:'openstreetmap',type:'raster',source:'openstreetmap',paint:{'raster-saturation':-0.72,'raster-contrast':-0.08,'raster-brightness-max':0.94}}]};

export default function CityMap({items,geo,providerKey,onLocation,onReportSelect,onAreaSelect,center,viewport,onViewport}:{items:ReportMarker[];geo:any;providerKey?:string;center?:Location;onLocation?:(p:Location)=>void;onReportSelect?:(id:string)=>void;onAreaSelect?:(id:string)=>void;viewport?:Viewport;onViewport?:(v:Viewport)=>void}){
 const root=useRef<HTMLDivElement>(null);const map=useRef<MapInstance|null>(null);
 const latest=useRef({items,geo,onLocation,onReportSelect,onAreaSelect,center,viewport,onViewport});latest.current={items,geo,onLocation,onReportSelect,onAreaSelect,center,viewport,onViewport};
 const [failed,setFailed]=useState(false);
 useEffect(()=>{
  if(!root.current)return;
  let instance:MapInstance;
  try{instance=new maplibregl.Map({container:root.current,style:providerKey?`https://api.maptiler.com/maps/streets-v2-light/style.json?key=${encodeURIComponent(providerKey)}`:localBaseStyle,center:[latest.current.viewport?.lng??latest.current.center?.lng??72.851,latest.current.viewport?.lat??latest.current.center?.lat??19.033],zoom:latest.current.viewport?.zoom??10.5,attributionControl:{compact:true}});}catch{setFailed(true);return;}
  map.current=instance;setFailed(false);
  const labels=new Map<number,maplibregl.Marker>();
  instance.addControl(new maplibregl.NavigationControl({showCompass:false}),'bottom-right');
  instance.on('load',()=>{
   instance.addSource('areas',{type:'geojson',data:latest.current.geo||{type:'FeatureCollection',features:[]}});
   instance.addLayer({id:'ward-fill',type:'fill',source:'areas',filter:['==',['get','type'],'ward'],paint:{'fill-color':'#d88282','fill-opacity':0.12}});
   instance.addLayer({id:'ward-borders',type:'line',source:'areas',paint:{'line-color':'#ba7777','line-width':1,'line-opacity':0.65}});
   instance.addSource('reports',{type:'geojson',data:points(latest.current.items),cluster:true,clusterRadius:48,clusterMaxZoom:15,clusterProperties:{resolved_count:['+',['case',['==',['get','status'],'resolved'],1,0]]}});
   instance.addLayer({id:'report-clusters',type:'circle',source:'reports',filter:['has','point_count'],paint:{'circle-color':['case',['==',['get','resolved_count'],['get','point_count']],'#287250',['>',['get','resolved_count'],0],'#896322','#933737'],'circle-opacity':0.94,'circle-radius':['step',['get','point_count'],22,10,27,100,33],'circle-stroke-width':2,'circle-stroke-color':'#ffffff'}});
   instance.addLayer({id:'report-points',type:'circle',source:'reports',filter:['!',['has','point_count']],paint:{'circle-radius':9,'circle-color':['case',['==',['get','status'],'resolved'],'#347257',['match',['get','severity'],'high','#b95045','medium','#cc7d39','#5d8558']],'circle-stroke-color':['case',['==',['get','status'],'resolved'],'#b9dbc5','#ffffff'],'circle-stroke-width':['case',['==',['get','status'],'resolved'],4,2]}});
  });
  // DOM labels only for visible clusters: no per-report DOM pins and no font provider
  // required in the credential-free geographic demo.
  const drawLabels=()=>{
   if(!instance.getLayer('report-clusters'))return;
   const visible=new Set<number>();
   for(const feature of instance.queryRenderedFeatures({layers:['report-clusters']})){
    const id=Number(feature.properties.cluster_id);if(visible.has(id)||feature.geometry.type!=='Point')continue;visible.add(id);
    const count=Number(feature.properties.point_count);
    let marker=labels.get(id);
    if(!marker){
     const button=document.createElement('button');button.type='button';button.className='map-cluster-count';
     button.addEventListener('click',async e=>{e.stopPropagation();try{const zoom=await (instance.getSource('reports') as GeoJSONSource).getClusterExpansionZoom(id);if(map.current===instance)instance.easeTo({center:marker!.getLngLat(),zoom});}catch{/* Source may have changed after filtering. */}});
     marker=new maplibregl.Marker({element:button}).setLngLat(feature.geometry.coordinates as [number,number]).addTo(instance);labels.set(id,marker);
    }
    marker.setLngLat(feature.geometry.coordinates as [number,number]);
    const resolved=Number(feature.properties.resolved_count)||0;
    const button=marker.getElement();button.textContent=count.toLocaleString('en-IN');button.setAttribute('aria-label',`Zoom into cluster of ${count} reports: ${count-resolved} unresolved, ${resolved} resolved`);button.dataset.status=resolved===count?'resolved':resolved?'mixed':'unresolved';
   }
   for(const [id,marker] of labels)if(!visible.has(id)){marker.remove();labels.delete(id);}
  };
  instance.on('render',drawLabels);
  instance.on('moveend',()=>{const p=instance.getCenter();latest.current.onViewport?.({lat:p.lat,lng:p.lng,zoom:instance.getZoom()});});
  instance.on('click',e=>{
   if(latest.current.onLocation){latest.current.onLocation({lat:e.lngLat.lat,lng:e.lngLat.lng});return;}
   if(!instance.getLayer('report-points'))return;
   const report=instance.queryRenderedFeatures(e.point,{layers:['report-points']})[0];
   if(report){latest.current.onReportSelect?.(String(report.properties.id));return;}
   const area=instance.queryRenderedFeatures(e.point,{layers:['ward-fill']})[0];
   if(area?.properties.id)latest.current.onAreaSelect?.(String(area.properties.id));
  });
  instance.on('mouseenter','report-points',()=>{instance.getCanvas().style.cursor='pointer';});
  instance.on('mouseleave','report-points',()=>{instance.getCanvas().style.cursor='';});
  return()=>{for(const marker of labels.values())marker.remove();instance.remove();map.current=null;};
 },[providerKey]);
 useEffect(()=>{const source=map.current?.getSource('reports') as GeoJSONSource|undefined;source?.setData(points(items));},[items]);
 useEffect(()=>{const source=map.current?.getSource('areas') as GeoJSONSource|undefined;if(geo)source?.setData(geo);},[geo]);
 useEffect(()=>{if(center&&map.current&&!latest.current.viewport){const current=map.current.getCenter();if(Math.abs(current.lng-center.lng)>0.000001||Math.abs(current.lat-center.lat)>0.000001)map.current.flyTo({center:[center.lng,center.lat],zoom:13,essential:false});}},[center]);
 return <><div ref={root} className="city-map" role="region" aria-label="Map of nearby civic reports. A list alternative is available."/>{failed&&<p role="status">The map could not load. Use the List view to explore reports.</p>}</>;
}
