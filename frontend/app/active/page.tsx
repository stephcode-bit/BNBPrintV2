"use client";

import { useState } from "react";
import StatsBar from "@/components/StatsBar";
import FilterBar from "@/components/FilterBar";
import LiveFeed from "@/components/LiveFeed";
import type { TokenFilters } from "@/lib/types";

// "Active" is a narrower lens on the same still-bonding feed as Dashboard:
// only tokens that already have real buyers in (more than just the
// creator wallet holding), via min_holder_count — see
// frontend/app/api/tokens/route.ts for the actual filter, and
// backend/app/services/goplus.py / chain_listener.py for where
// holder_count itself comes from.
export default function ActivePage() {
  const [filters, setFilters] = useState<TokenFilters>({
    bonding: true,
    min_holder_count: 2,
    sort_by: "created_at",
    order: "desc",
    limit: 60,
    offset: 0,
  });

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="font-display font-bold text-2xl sm:text-3xl text-white">Active Bonding</h1>
        <p className="text-sm text-bnb-muted mt-1 max-w-2xl">
          Still-bonding tokens that already have real buyers in — more than just the creator holding.
          A higher-signal slice of the full Dashboard feed, for skipping past ones nobody's touched yet.
        </p>
      </div>

      <StatsBar />
      <FilterBar filters={filters} onChange={setFilters} lockBonding />
      <LiveFeed filters={filters} />
    </div>
  );
}
