import type {Metadata,Viewport} from 'next';
import Providers from '@/components/providers';
import './globals.css';
import './mobile-v1.css';
export const metadata:Metadata={title:{default:'CivicQuest — Level up your city',template:'%s · CivicQuest'},description:'Small acts. Real impact. Discover civic issues, join local cleanups, and help make Mumbai better.',manifest:'/manifest.webmanifest',icons:{icon:'/icon.svg',apple:'/icon.svg'}};
export const viewport:Viewport={width:'device-width',initialScale:1,themeColor:'#f7f8f2'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body><Providers>{children}</Providers></body></html>;}
