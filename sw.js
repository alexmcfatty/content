// Network first, so edits (including rules.txt) show up straight away; cache is the offline fallback.
const CACHE = 'content-bank-v2';
const SHELL = ['./', 'index.html', 'config.js', 'rules.txt', 'manifest.json', 'icons/icon-192.png', 'icons/icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  const mine = url.origin === location.origin;
  const lib = url.hostname === 'cdn.jsdelivr.net';
  if (e.request.method !== 'GET' || (!mine && !lib)) return; // never touch Supabase calls
  e.respondWith(
    fetch(e.request).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
      return res;
    }).catch(() => caches.match(e.request))
  );
});
