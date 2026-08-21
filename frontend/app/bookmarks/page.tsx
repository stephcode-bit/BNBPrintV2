"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { BookmarkX } from "lucide-react";
import { api } from "@/lib/api";
import { getLocalBookmarks } from "@/lib/bookmarks";
import TokenCard from "@/components/TokenCard";
import TokenCardSkeleton from "@/components/TokenCardSkeleton";

export default function BookmarksPage() {
  // Bookmarks live in localStorage (see lib/bookmarks.ts) — this page just
  // cross-references those saved addresses against the live token snapshot
  // to render full cards, rather than fetching a per-user list from a
  // server (there isn't one — see the $0/month rework).
  const [addresses, setAddresses] = useState<Set<string> | null>(null);

  useEffect(() => {
    setAddresses(getLocalBookmarks());
  }, []);

  const { data, isLoading } = useQuery({
    queryKey: ["tokens", "for-bookmarks"],
    queryFn: () => api.listTokens({ limit: 200 }),
    enabled: addresses !== null,
    refetchInterval: 20_000,
  });

  const tokens = (data?.items || []).filter((t) => addresses?.has(t.address.toLowerCase()));

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="font-display font-bold text-2xl sm:text-3xl text-white">Your Watchlist</h1>
        <p className="text-sm text-bnb-muted mt-1">
          Bookmarked tokens, saved to this device. Everything here updates as bonding progress and
          security scores change.
        </p>
      </div>

      {isLoading || addresses === null ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <TokenCardSkeleton key={i} />
          ))}
        </div>
      ) : tokens.length === 0 ? (
        <div className="rounded-xl border border-dashed border-bnb-border p-12 text-center">
          <BookmarkX className="mx-auto mb-3 text-bnb-muted" size={28} />
          <p className="text-sm text-bnb-muted">
            No bookmarks yet. Tap the bookmark icon on any token card to save it here for later review.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
          {tokens.map((token) => (
            <TokenCard key={token.address} token={token} />
          ))}
        </div>
      )}
    </div>
  );
}
