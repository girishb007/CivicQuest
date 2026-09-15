'use client';

import {useQuery} from '@tanstack/react-query';
import {ArrowRight, Compass, List, LocateFixed, Map as MapIcon, MapPin, Navigation, Plus, Search, ShieldCheck, X} from 'lucide-react';
import Link from 'next/link';
import {useEffect, useRef, useState} from 'react';

import {useExploreState} from '@/lib/explore-state';
import {api, locate, pretty} from '@/lib/api';
import CityMap from './city-map';

type Props = {cfg: any; notify: (message: string) => void};
type Selection = {kind: 'report' | 'area'; id: string} | null;

function LoadingMap() {
  return <div className="state"><Compass className="spin"/><p>Loading the civic map…</p></div>;
}

function Severity({value}: {value?: string}) {
  const severity = value || 'medium';
  return <span className={`severity-pill ${severity}`}>{severity} severity</span>;
}

function ReportSheet({report, close}: {report: any; close: () => void}) {
  const focus = useRef<HTMLButtonElement>(null);
  useEffect(() => { focus.current?.focus(); }, []);
  return <div className="map-sheet" role="dialog" aria-modal="false" aria-label={`${report.title} preview`}><section><div className="sheet-handle"/><button ref={focus} className="sheet-close icon-button" aria-label="Close report preview" onClick={close}><X size={18}/></button><div className="sheet-preview">{report.image_url ? <img src={report.image_url} alt=""/> : <div className="photo-placeholder"><MapPin/></div>}<div><Severity value={report.severity}/><h2>{report.title}</h2><p>{report.address}</p></div></div><div className="sheet-stats"><span>{pretty(report.status)}</span><span>{report.seen_count || 0} Seen</span><span>{new Date(report.created_at).toLocaleDateString('en-IN')}</span></div><div className="sheet-actions"><Link className="button dark" href={`/i/${report.public_code}`}>Open report <ArrowRight size={15}/></Link></div></section></div>;
}

function AreaSheet({id, close}: {id: string; close: () => void}) {
  const query = useQuery({queryKey: ['area-sheet', id], queryFn: () => api(`/areas/${id}`)});
  const area = query.data;
  return <div className="map-sheet" role="dialog" aria-modal="false" aria-label="Ward preview"><section><div className="sheet-handle"/><button className="sheet-close icon-button" aria-label="Close ward preview" onClick={close}><X size={18}/></button>{query.isPending ? <p>Loading ward context…</p> : query.isError ? <p>Ward context is temporarily unavailable.</p> : <><span className="kicker">{pretty(area.area_type)} · {area.code}</span><h2>{area.name}</h2><div className="sheet-stats"><span>{area.statistics.active} active</span><span>{area.statistics.resolved} resolved</span><span>{area.statistics.total_reports} public reports</span></div><p>{area.statistics.boundary_note}</p><div className="sheet-actions"><Link className="button dark" href={`/areas/${id}`}>View ward <ArrowRight size={15}/></Link></div></>}</section></div>;
}

function ReportList({items, select}: {items: any[]; select: (id: string) => void}) {
  if (!items.length) return <div className="state"><MapPin/><p>No matching reports are loaded in this area.</p></div>;
  return <div className="map-list mobile-report-list">{items.map((item) => <button key={item.id} onClick={() => select(item.id)}><span className={`marker-symbol ${item.status === 'resolved' ? 'resolved' : item.severity}`}><MapPin size={15}/></span><span><strong>{item.title}</strong><small>{item.address}</small><span><Severity value={item.severity}/>{pretty(item.status)} · {item.seen_count || 0} Seen</span></span><ArrowRight size={16}/></button>)}</div>;
}

export function ExploreScreen({cfg, notify}: Props) {
  const {state, set, ready} = useExploreState();
  const {center, radius, list, search, filter, status, viewport} = state;
  const [selection, setSelection] = useState<Selection>(null);
  const [matches, setMatches] = useState<any[]>([]);
  const [postalContext, setPostalContext] = useState<any>(null);
  const family = filter === 'all' ? '' : `&family=${filter}`;
  const nearby = useQuery({
    queryKey: ['mobile-explore', center.lat, center.lng, radius, filter, status],
    queryFn: () => api(`/explore?radius_m=${radius}&lat=${center.lat}&lng=${center.lng}&status=${status}${family}`),
    enabled: ready,
  });
  const geometry = useQuery({queryKey: ['geography'], queryFn: () => api('/geography')});
  const items = nearby.data?.reports || [];
  const selectedReport = selection?.kind === 'report' ? items.find((item: any) => item.id === selection.id) : null;

  useEffect(() => {
    const close = () => setSelection(null);
    window.addEventListener('popstate', close);
    return () => window.removeEventListener('popstate', close);
  }, []);

  function select(next: Selection) {
    setSelection(next);
    if (next) window.history.pushState({civicQuestSheet: true}, '', `#${next.kind}=${next.id}`);
  }
  function close() {
    if (window.location.hash.startsWith('#report=') || window.location.hash.startsWith('#area=')) window.history.back();
    else setSelection(null);
  }
  async function searchArea() {
    if (!search.trim()) return;
    try {
      setMatches((await api(`/places/search?q=${encodeURIComponent(search)}`)).items);
    } catch (caught: any) {
      notify(caught.message);
    }
  }
  async function chooseMatch(match: any) {
    set('search', match.name); setMatches([]); set('center', {lat: match.lat, lng: match.lng});
    set('viewport', undefined); set('radius', 3000); setPostalContext(null);
    if (match.area_type === 'postal_place') {
      try {
        const context = await api(`/administrative-areas/lookup?lat=${match.lat}&lng=${match.lng}`);
        setPostalContext({...context, pincode: match.pincode, office: match.name, source_url: match.source_url});
      } catch (caught: any) { notify(caught.message); }
    }
  }

  return <>
    <section className="mobile-map-head">
      <div><span className="kicker">MUMBAI CIVIC MAP</span><h1>Explore your area</h1></div>
      <div className="map-top-counts"><span><strong>{nearby.data?.summary?.active ?? '—'}</strong>active</span><span><strong>{nearby.data?.summary?.resolved ?? '—'}</strong>resolved</span></div>
    </section>
    <section className="map-panel">
      <div className="map-toolbar mobile-map-toolbar">
        <div className="map-search"><Search size={16}/><input aria-label="Search Mumbai area" placeholder="Search ward or neighbourhood" value={search} onChange={(event) => set('search', event.target.value)} onKeyDown={(event) => event.key === 'Enter' && searchArea()}/><button aria-label="Search" onClick={searchArea}><ArrowRight size={17}/></button></div>
        {matches.length > 0 && <div className="search-results">{matches.map((match: any, index: number) => <button key={index} onClick={() => chooseMatch(match)}><MapPin size={14}/>{match.name}</button>)}</div>}
        <div className="map-controls">
          <label>Category<select aria-label="Map issue type" value={filter} onChange={(event) => set('filter', event.target.value)}><option value="all">All issues</option><option value="waste">Waste</option><option value="roads">Roads</option><option value="lighting">Streetlights</option><option value="water">Water</option><option value="drainage">Drainage</option></select></label>
          <label>Status<select aria-label="Map report status" value={status} onChange={(event) => set('status', event.target.value)}><option value="active">Active</option><option value="resolved">Resolved</option><option value="all">All status</option></select></label>
          <div className="segmented"><button className={!list ? 'selected' : ''} aria-label="Map view" onClick={() => set('list', false)}><MapIcon size={14}/></button><button className={list ? 'selected' : ''} aria-label="List view" onClick={() => set('list', true)}><List size={14}/></button></div>
        </div>
      </div>
      {postalContext&&<aside className="postal-context" aria-live="polite"><ShieldCheck/><div><strong>{postalContext.office}</strong><p>{postalContext.ambiguous?'This post office lies on a shared ward edge. Choose the location carefully.':'Resolved from this India Post office point.'}</p><div>{postalContext.areas.filter((area:any)=>area.type!=='city').map((area:any)=><Link href={`/areas/${area.id}`} key={area.id}>{area.name}<small>{pretty(area.type)}</small></Link>)}</div><a href={postalContext.source_url} target="_blank" rel="noreferrer">Department of Posts source</a></div></aside>}
      {!ready || nearby.isPending || geometry.isPending ? <LoadingMap/> : list ? <ReportList items={items} select={(id) => select({kind: 'report', id})}/> : <CityMap items={items} geo={geometry.data} providerKey={cfg.maptiler_key} center={center} viewport={viewport} onViewport={(next) => set('viewport', next)} onReportSelect={(id) => select({kind: 'report', id})} onAreaSelect={(id) => select({kind: 'area', id})}/>} 
      <div className="map-civic-legend"><span><i className="low"/>Low</span><span><i className="medium"/>Medium</span><span><i className="high"/>High</span><span><i className="resolved"/>Resolved</span><button onClick={async () => { try { const position = await locate(); set('center', position); set('viewport', undefined); set('radius', 3000); notify('Showing reports near your location.'); } catch (caught: any) { notify(caught.message); } }}><LocateFixed size={14}/>Locate</button></div>
    </section>
    <Link className="floating-capture" href="/capture"><Plus size={21}/>Capture</Link>
    {selection?.kind === 'report' && selectedReport && <ReportSheet report={selectedReport} close={close}/>} 
    {selection?.kind === 'area' && <AreaSheet id={selection.id} close={close}/>} 
  </>;
}
