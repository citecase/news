/**
 * CiteCase Service Worker v3.0.0
 * Optimized for aggressive updates and fresh legal data.
 */

const CACHE_NAME = 'citecase-v3-cache';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

// Install Event - Force the new service worker to become active immediately
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

// Activate Event - Clean up old caches and take control of all tabs
self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      // Take control of all open clients (tabs) immediately
      clients.claim(),
      // Remove old versions of the cache
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              return caches.delete(cacheName);
            }
          })
        );
      })
    ])
  );
});

// Fetch Event - Dynamic strategy
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 1. For news data, ALWAYS try the network first to ensure updates show up
  if (url.pathname.includes('news.json')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Update the cache with the fresh news
          const clonedResponse = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clonedResponse));
          return response;
        })
        .catch(() => caches.match(event.request)) // Fallback to cache if offline
    );
    return;
  }

  // 2. For UI assets (HTML, CSS, Icons), use Stale-While-Revalidate
  // This serves from cache fast but updates the cache in the background
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const networkFetch = fetch(event.request).then((networkResponse) => {
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, networkResponse.clone());
        });
        return networkResponse;
      });
      return cachedResponse || networkFetch;
    })
  );
});
