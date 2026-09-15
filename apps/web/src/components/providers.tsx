'use client';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {useEffect,useState} from 'react';
export default function Providers({children}:{children:React.ReactNode}){
 const [client]=useState(()=>new QueryClient({defaultOptions:{queries:{staleTime:15000,retry:1,refetchOnWindowFocus:false}}}));
 useEffect(()=>{if('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(()=>{});},[]);
 return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
