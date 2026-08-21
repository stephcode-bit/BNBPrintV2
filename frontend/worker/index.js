/* eslint-disable no-restricted-globals */
// Custom service worker source for BNBPRINT.
// next-pwa (in InjectManifest mode, via swSrc in next.config.js) bundles
// this file and injects the precache manifest at `self.__WB_MANIFEST`.
// This is where BNBPRINT-specific behavior lives on top of the default
// app-shell precaching: runtime API caching + Web Push (VAPID) alerts.
import { clientsClaim } from "workbox-core";
import { precacheAndRoute } from "workbox-precaching";
import { registerRoute } from "workbox-routing";
import { NetworkFirst } from "workbox-strategies";
import { ExpirationPlugin } from "workbox-expiration";

self.skipWaiting();
clientsClaim();

precacheAndRoute(self.__WB_MANIFEST || []);

// Live token feed + stats: prefer fresh data, fall back to the last good
// response when offline so the dashboard still shows something useful.
registerRoute(
  ({ url }) => url.pathname.startsWith("/api/tokens"),
  new NetworkFirst({
    cacheName: "bnbprint-tokens-cache",
    networkTimeoutSeconds: 5,
    plugins: [new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 5 * 60 })],
  })
);

registerRoute(
  ({ url }) => url.pathname.startsWith("/api/stats"),
  new NetworkFirst({
    cacheName: "bnbprint-stats-cache",
    networkTimeoutSeconds: 5,
    plugins: [new ExpirationPlugin({ maxEntries: 10, maxAgeSeconds: 5 * 60 })],
  })
);

// Web Push (standard PWA push via VAPID — no Firebase). The backend sends
// a JSON payload: { title, body, url }. See app/services/push.py.
self.addEventListener("push", (event) => {
  let payload = { title: "BNBPRINT", body: "New alert", url: "/" };
  try {
    if (event.data) payload = { ...payload, ...event.data.json() };
  } catch {
    // non-JSON payload, fall back to defaults
  }

  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      icon: "/icons/icon-192.png",
      badge: "/icons/icon-192.png",
      data: { url: payload.url || "/" },
      tag: "bnbprint-alert",
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || "/";

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if (client.url.includes(targetUrl) && "focus" in client) return client.focus();
      }
      if (self.clients.openWindow) return self.clients.openWindow(targetUrl);
    })
  );
});
