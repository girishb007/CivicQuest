import type {Metadata} from 'next';
import App from '@/components/app';
export const dynamic='force-dynamic';
type Props={params:Promise<{path?:string[]}>};
async function publicReport(path?:string[]){
 const key=path?.[1];
 if(!key||!['reports','i'].includes(path?.[0]||''))return undefined;
 const endpoint=path?.[0]==='i'?`reports/by-code/${encodeURIComponent(key)}`:`reports/${encodeURIComponent(key)}`;
 try{const r=await fetch(`${process.env.API_INTERNAL_URL||'http://localhost:8000'}/api/v1/${endpoint}`,{cache:'no-store'});return r.ok?await r.json():undefined;}catch{return undefined;}
}
export async function generateMetadata({params}:Props):Promise<Metadata>{const {path}=await params;const report=await publicReport(path);return report?{title:report.title,description:report.description,robots:{index:!report.demo,follow:true}}:{robots:{index:!path?.length,follow:true}};}
export default async function Page({params}:Props){const {path}=await params;return <App initialReport={await publicReport(path)}/>;}
