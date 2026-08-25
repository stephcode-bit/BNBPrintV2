"use client";

import { useState } from "react";
import StatsBar from "@/components/StatsBar";
import FilterBar from "@/components/FilterBar";
import LiveFeed from "@/components/LiveFeed";
import type { TokenFilters } from "@/lib/types";

// Tokens whose bonding curve finished and migrated to a real DEX pool
// (is_bonding flips to false). They no longer show on the Dashboard tab —
// this is where they live instead, so Dashboard stays focused on tokens
// still actively bonding.
export default function MigratedPage() {
  const [filters, setFilters] = useState<TokenFilters>({
    bonding: false,
    sort_by: "created_at",
    order: "desc",
    limit: 60,
    offset: 0,
  });

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="font-display font-bold text-2xl sm:text-3xl text-white">Migrated</h1>
        <p className="text-sm text-bnb-muted mt-1 max-w-2xl">
          Tokens that finished bonding and moved to a live DEX pool. Pulled off the Dashboard feed
          automatically once they graduate, so the Dashboard stays focused on tokens still in progress.
        </p>
      </div>

      <StatsBar />
      <FilterBar filters={filters} onChange={setFilters} lockBonding />
      <LiveFeed filters={filters} />
    </div>
  );
}
