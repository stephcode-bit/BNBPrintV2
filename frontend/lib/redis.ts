import { Redis } from "@upstash/redis";

/**
 * Same Upstash Redis database the scanner (backend/scan_runner.py, run by
 * .github/workflows/scanner.yml) writes to — see backend/app/services/
 * store.py for the key layout this mirrors. Reading it directly here
 * (rather than proxying to a hosted API) is what lets the frontend run
 * with zero always-on backend at all.
 */
let client: Redis | null = null;

export function getRedis(): Redis | null {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) return null;
  if (!client) client = new Redis({ url, token });
  return client;
}
