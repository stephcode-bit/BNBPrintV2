const withPWA = require("next-pwa")({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
  // Custom SW source (adds Web Push handling on top of the default asset
  // caching) — see worker/index.js. Runtime caching rules for /api/tokens
  // and /api/stats live inside that file (via workbox-routing) rather than
  // here, since InjectManifest mode (triggered by swSrc) doesn't support
  // the `runtimeCaching` option that GenerateSW mode uses.
  swSrc: "worker/index.js",
  fallbacks: {
    document: "/offline",
  },
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },
  // No vercel.json needed for this project — Vercel auto-detects Next.js
  // with zero config. The one thing worth being deliberate about for a
  // PWA is cache-control on the service worker itself: if a CDN caches
  // sw.js aggressively, users can get stuck on a stale service worker
  // after you redeploy. Setting this here (rather than in vercel.json)
  // keeps it portable to any host, not just Vercel.
  async headers() {
    return [
      {
        source: "/sw.js",
        headers: [{ key: "Cache-Control", value: "public, max-age=0, must-revalidate" }],
      },
      {
        source: "/manifest.json",
        headers: [{ key: "Cache-Control", value: "public, max-age=0, must-revalidate" }],
      },
    ];
  },
};

module.exports = withPWA(nextConfig);
