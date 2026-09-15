const SHELL='civicquest-shell-v1';
self.addEventListener('install',e=>{e.waitUntil(caches.open(SHELL).then(c=>c.addAll(['/offline.html','/icon.svg'])));self.skipWaiting();});
self.addEventListener('activate',e=>e.waitUntil(Promise.all([self.clients.claim(),caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==SHELL).map(k=>caches.delete(k))))])));
self.addEventListener('fetch',e=>{if(e.request.mode==='navigate')e.respondWith(fetch(e.request).catch(()=>caches.match('/offline.html')));});
self.addEventListener('push',e=>{let payload={};try{payload=e.data.json();}catch{}e.waitUntil(self.registration.showNotification(payload.title||'CivicQuest update',{body:payload.body||'Open CivicQuest to see your update.',icon:'/icon.svg',tag:payload.tag||'civicquest',data:{href:'/notifications'}}));});
self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(self.clients.openWindow('/notifications'));});
