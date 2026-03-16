self.addEventListener('install', (event) => {
    console.log('[Service Worker] Install');
});

self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activate');
});

self.addEventListener('fetch', (event) => {
    // Chrome requires a fetch event handler to consider the app installable (PWA)
    // We don't cache anything for offline use right now, just pass the request through.
    event.respondWith(fetch(event.request).catch(() => {
        return new Response('Offline mode not fully supported yet.');
    }));
});
