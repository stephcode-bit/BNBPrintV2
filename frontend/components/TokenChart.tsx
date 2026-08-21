"use client";

import { useEffect, useRef, useState } from "react";
import type { Token } from "@/lib/types";
import { formatUsd } from "@/lib/utils";
import Sparkline from "./Sparkline";

interface Snapshot {
  market_cap_usd: number;
  volume_24h_usd: number;
  holder_count: number;
}

const MAX_POINTS = 60;

export default function TokenChart({ token }: { token: Token }) {
  const [history, setHistory] = useState<Snapshot[]>([]);
  const lastAddress = useRef<string | null>(null);

  useEffect(() => {
    // Reset the session history when navigating to a different token.
    if (lastAddress.current !== token.address) {
      lastAddress.current = token.address;
      setHistory([
        { market_cap_usd: token.market_cap_usd, volume_24h_usd: token.volume_24h_usd, holder_count: token.holder_count },
      ]);
      return;
    }
    setHistory((prev) => {
      const next = [
        ...prev,
        { market_cap_usd: token.market_cap_usd, volume_24h_usd: token.volume_24h_usd, holder_count: token.holder_count },
      ];
      return next.slice(-MAX_POINTS);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token.market_cap_usd, token.volume_24h_usd, token.holder_count, token.address]);

  return (
    <div className="rounded-xl border border-bnb-border bg-bnb-panel/60 p-4">
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-display font-semibold text-sm text-white">Live Session Chart</h3>
        <span className="text-[10px] text-bnb-muted font-mono">
          {history.length} snapshot{history.length === 1 ? "" : "s"} this session
        </span>
      </div>
      <p className="text-xs text-bnb-muted mb-3">
        Builds in real time from live updates while this page is open — not historical OHLC data.
      </p>

      <ChartRow label="Market Cap" value={formatUsd(token.market_cap_usd)} values={history.map((h) => h.market_cap_usd)} color="#F0B90B" />
      <ChartRow label="Volume 24h" value={formatUsd(token.volume_24h_usd)} values={history.map((h) => h.volume_24h_usd)} color="#0ECB81" />
      <ChartRow label="Holders" value={String(token.holder_count)} values={history.map((h) => h.holder_count)} color="#848E9C" />
    </div>
  );
}

function ChartRow({ label, value, values, color }: { label: string; value: string; values: number[]; color: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2 border-t border-bnb-border/40 first:border-0">
      <div>
        <div className="text-[10px] uppercase tracking-wide text-bnb-muted">{label}</div>
        <div className="font-mono font-bold tabular text-white">{value}</div>
      </div>
      <Sparkline values={values} width={160} height={40} color={color} />
    </div>
  );
}
