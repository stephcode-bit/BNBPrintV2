"use client";

import { Bookmark } from "lucide-react";
import clsx from "clsx";
import { addLocalBookmark, isBookmarkedLocally, removeLocalBookmark } from "@/lib/bookmarks";
import { useEffect, useState } from "react";

/**
 * Bookmarks are per-device, stored in localStorage only (see
 * lib/bookmarks.ts) — no server round-trip. There's no per-user backend
 * anymore (see the $0/month rework), and a device-local watchlist is a
 * reasonable trade for a free tool like this; swap for a synced version
 * later if you add real accounts.
 */
export default function BookmarkButton({ address, className }: { address: string; className?: string }) {
  const [isBookmarked, setIsBookmarked] = useState(false);

  useEffect(() => {
    setIsBookmarked(isBookmarkedLocally(address));
  }, [address]);

  function toggle(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (isBookmarked) {
      removeLocalBookmark(address);
      setIsBookmarked(false);
    } else {
      addLocalBookmark(address);
      setIsBookmarked(true);
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isBookmarked ? "Remove bookmark" : "Add to watchlist"}
      aria-pressed={isBookmarked}
      className={clsx(
        "inline-flex items-center justify-center rounded-md border min-w-[44px] min-h-[36px] w-9 h-9 transition-all",
        isBookmarked
          ? "border-bnb-yellow/50 bg-bnb-yellow/10 text-bnb-yellow"
          : "border-bnb-border bg-bnb-panel text-bnb-muted hover:text-bnb-yellow hover:border-bnb-yellow/40",
        className
      )}
    >
      <Bookmark size={15} fill={isBookmarked ? "currentColor" : "none"} />
    </button>
  );
}
