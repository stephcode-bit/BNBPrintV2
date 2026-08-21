"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatUsd, shortAddress } from "@/lib/utils";
import { useTokenStream } from "@/lib/ws";
import type { Token } from "@/lib/types";
import Link from "next/link";
import clsx from "clsx";

const MAX_ITEMS = 16;

export default function TickerTape() {
  const { data } = useQuery({
    queryKey: ["ticker-tokens"],
    queryFn: () => api.listTokens({ sort_by: "created_at", order: "desc", limit: MAX_ITEMS }),
    refetchInterval: 30_000,
  });
  const { subscribe } = useTokenStream();
  const [items, setItems] = useState<Token[]>([]);

  useEffect(() => {
    if (data?.items) setItems(data.items.slice(0, MAX_ITEMS));
  }, [data]);

  useEffect(() => {
    return subscribe((event) => {
      if (event.type !== "new_token") return;
      setItems((prev) => [event.data, ...prev.filter((t) => t.address !== event.data.address)].slice(0, MAX_ITEMS));
    });
  }, [subscribe]);

  if (items.length === 0) return null;

  const loop = [...items, ...items];

  return (
    <div className="w-full overflow-hidden border-b border-bnb-border/60 bg-bnb-dark/80">
      <div className="ticker-track flex w-max gap-0 whitespace-nowrap py-1.5">
        {loop.map((t, i) => (
          <Link
            href={`/token/${t.address}`}
            key={`${t.address}-${i}`}
            className="flex items-center gap-2 px-4 border-r border-bnb-border/40 text-xs hover:bg-white/5 transition-colors"
          >
            <span className={clsx("h-1.5 w-1.5 rounded-full", t.is_runner ? "bg-bnb-yellow animate-pulse" : "bg-bnb-muted/50")} />
            <span className="font-mono font-semibold text-bnb-yellow">{t.symbol}</span>
            <span className="text-bnb-muted font-mono">{shortAddress(t.address)}</span>
            <span className="tabular text-bnb-green">{formatUsd(t.market_cap_usd)}</span>
            <span className="tabular text-bnb-muted">{t.bonding_progress.toFixed(0)}%</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
