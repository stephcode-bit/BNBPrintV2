const KEY = "bnbprint_user_id";

/**
 * Anonymous, per-device identifier used for bookmarks (and push
 * subscriptions) without requiring an account. Persisted in localStorage;
 * swap this out for a real auth-derived id later if you add accounts.
 */
export function getUserId(): string {
  if (typeof window === "undefined") return "server";
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(KEY, id);
  }
  return id;
}
