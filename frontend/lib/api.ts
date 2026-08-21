import type { Stats, Token, TokenFilters, TokenListResponse } from "./types";

/**
 * All routes below are same-origin Next.js API routes (see app/api/*) that
 * read/write Upstash Redis directly — there's no separate backend to point
 * a base URL at anymore, so every path here is relative.
 */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function buildTokenQuery(filters: TokenFilters): string {
  const params = new URLSearchParams();
  if (filters.bonding !== undefined) params.set("bonding", String(filters.bonding));
  if (filters.platform) params.set("platform", filters.platform);
  if (filters.min_security_score !== undefined)
    params.set("min_security_score", String(filters.min_security_score));
  if (filters.runners_only) params.set("runners_only", "true");
  if (filters.search) params.set("search", filters.search);
  if (filters.sort_by) params.set("sort_by", filters.sort_by);
  if (filters.order) params.set("order", filters.order);
  params.set("limit", String(filters.limit ?? 50));
  params.set("offset", String(filters.offset ?? 0));
  return params.toString();
}

export const api = {
  listTokens: (filters: TokenFilters = {}) =>
    request<TokenListResponse>(`/api/tokens?${buildTokenQuery(filters)}`),

  getToken: (address: string) => request<Token>(`/api/tokens/${address}`),

  getStats: () => request<Stats>("/api/stats"),

  // Bookmarks are pure client-side (localStorage — see lib/bookmarks.ts):
  // no server round-trip, so no watchlist needs to survive here.

  getVapidPublicKey: () => request<{ publicKey: string }>("/api/push/vapid-public-key"),

  subscribePush: (userId: string, sub: PushSubscriptionJSON) =>
    request("/api/push/subscribe", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        endpoint: sub.endpoint,
        p256dh: sub.keys?.p256dh,
        auth: sub.keys?.auth,
      }),
    }),

  unsubscribePush: (endpoint: string) =>
    request(`/api/push/unsubscribe?endpoint=${encodeURIComponent(endpoint)}`, { method: "DELETE" }),
};
