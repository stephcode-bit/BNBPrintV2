const KEY = "bnbprint_bookmarks_cache";

/**
 * Lightweight localStorage mirror of the user's bookmarked addresses.
 * The backend (via /api/bookmarks, keyed by the anonymous user id from
 * lib/userId.ts) is the source of truth so bookmarks show up in the
 * `/bookmarks` page with full token data — this cache just makes the
 * bookmark toggle feel instant and keeps working offline.
 */
export function getLocalBookmarks(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = localStorage.getItem(KEY);
    return new Set(raw ? (JSON.parse(raw) as string[]) : []);
  } catch {
    return new Set();
  }
}

function persist(set: Set<string>) {
  localStorage.setItem(KEY, JSON.stringify([...set]));
}

export function isBookmarkedLocally(address: string): boolean {
  return getLocalBookmarks().has(address.toLowerCase());
}

export function addLocalBookmark(address: string): void {
  const set = getLocalBookmarks();
  set.add(address.toLowerCase());
  persist(set);
}

export function removeLocalBookmark(address: string): void {
  const set = getLocalBookmarks();
  set.delete(address.toLowerCase());
  persist(set);
}
