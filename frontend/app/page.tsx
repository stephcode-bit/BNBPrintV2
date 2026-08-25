"use client";

import { useState } from "react";
import StatsBar from "@/components/StatsBar";
import FilterBar from "@/components/FilterBar";
import LiveFeed from "@/components/LiveFeed";
import type { TokenFilters } from "@/lib/types";

export default function DashboardPage() {
  // Dashboard is the "still bonding" feed only — once a token migrates it
  // moves to the dedicated Migrated tab instead (see app/migrated/page.tsx)
  // rather than lingering here alongside fresh launches.
  const [filters, setFilters] = useState<TokenFilters>({
    bonding: true,
    sort_by: "created_at",
    order: "desc",
    limit: 60,
    offset: 0,
  });

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="font-display font-bold text-2xl sm:text-3xl text-white">
          Runner Radar
        </h1>
        <p className="text-sm text-bnb-muted mt-1 max-w-2xl">
          Live-scanning BNB Chain bonding-curve launches — four.meme, GraFun, and PancakeSwap — flagging
          likely runners before they finish bonding, and screening every token for honeypots, rugs, and
          thin liquidity. Tokens that finish bonding move to the Migrated tab.
        </p>
      </div>

      <StatsBar />
      <FilterBar filters={filters} onChange={setFilters} lockBonding />
      <LiveFeed filters={filters} />
    </div>
  );
}
