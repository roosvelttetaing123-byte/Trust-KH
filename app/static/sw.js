// Cache the static app shell only. Never cache requests, API results, images or credentials.
const CACHE='trust-kh-shell-v1';
const ASSETS=['/','/index.html','/style.css','/app.js','/i18n.js','/icon.svg','/manifest.webmanifest'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)));self.skipWaiting();});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener('fetch',event=>{
 const url=new URL(event.request.url);
 if(event.request.method!=='GET'||url.origin!==self.location.origin||url.search||!ASSETS.includes(url.pathname))return;
 event.respondWith(fetch(event.request).catch(()=>caches.match(url.pathname)));
});
