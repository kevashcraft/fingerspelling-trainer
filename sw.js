/* ASL Fingerspelling Trainer - service worker
   - Precaches the app shell on install so the tool opens offline.
   - Serves audio clips cache-first, storing each clip the first time it's
     fetched. Combined with the page's background prefetch, the whole bank
     ends up cached and the app works fully offline.
   Bump CACHE_VERSION whenever index.html, sw.js, or the icons change so
   returning visitors pick up the new files. */

const CACHE_VERSION = 'v1';
const SHELL_CACHE = 'fs-shell-' + CACHE_VERSION;
const AUDIO_CACHE = 'fs-audio-' + CACHE_VERSION;   // kept across versions on purpose

// Relative URLs resolve against the SW's own location (the repo root on
// GitHub Pages project sites), so this works at /<user>.github.io/<repo>/.
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((k) => k.startsWith('fs-shell-') && k !== SHELL_CACHE)
          .map((k) => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

function isAudio(url) {
  return url.pathname.includes('/audio/') && url.pathname.endsWith('.mp3');
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // don't touch cross-origin

  // Audio: cache-first, populate on demand.
  if (isAudio(url)) {
    event.respondWith(
      caches.open(AUDIO_CACHE).then(async (cache) => {
        const hit = await cache.match(req);
        if (hit) return hit;
        try {
          const res = await fetch(req);
          if (res && res.ok) cache.put(req, res.clone());
          return res;
        } catch (err) {
          return hit || Response.error();
        }
      })
    );
    return;
  }

  // App shell / everything else: cache-first, then network,
  // then fall back to the cached index for navigations when offline.
  event.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).catch(() => {
      if (req.mode === 'navigate') return caches.match('./index.html');
      return Response.error();
    }))
  );
});
