"use client";

import { useState } from "react";
import StatsBar from "@/components/StatsBar";
import FilterBar from "@/components/FilterBar";
import LiveFeed from "@/components/LiveFeed";
import type { TokenFilters } from "@/lib/types";

export default function DashboardPage() {
  const [filters, setFilters] = useState<TokenFilters>({
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
          thin liquidity.
        </p>
      </div>

      <StatsBar />
      <FilterBar filters={filters} onChange={setFilters} />
      <LiveFeed filters={filters} />
    </div>
  );
}
