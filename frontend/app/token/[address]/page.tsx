"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useParams } from "next/navigation";
import { ExternalLink, Flame } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useTokenStream } from "@/lib/ws";
import { bscScanUrl, formatAge, formatUsd, shortAddress } from "@/lib/utils";
import CopyButton from "@/components/CopyButton";
import BookmarkButton from "@/components/BookmarkButton";
import SecurityBadge from "@/components/SecurityBadge";
import BondingProgressBar from "@/components/BondingProgressBar";
import SecurityChecklist from "@/components/SecurityChecklist";
import TokenChart from "@/components/TokenChart";

export default function TokenDetailPage() {
  const params = useParams<{ address: string }>();
  const address = params.address;
  const queryClient = useQueryClient();
  const { subscribe } = useTokenStream();

  const queryKey = ["token", address];
  const { data: token, isLoading, isError } = useQuery({
    queryKey,
    queryFn: () => api.getToken(address),
    refetchInterval: 30_000,
  });

  useEffect(() => {
    return subscribe((event) => {
      if (event.data.address.toLowerCase() !== address.toLowerCase()) return;
      queryClient.setQueryData(queryKey, event.data);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subscribe, address]);

  if (isLoading) {
    return <div className="animate-pulse text-bnb-muted text-sm">Loading token…</div>;
  }

  if (isError || !token) {
    return (
      <div className="rounded-xl border border-bnb-red/30 bg-bnb-red/5 p-8 text-center">
        <p className="text-sm text-bnb-red mb-2">Token not found.</p>
        <Link href="/" className="text-xs text-bnb-yellow underline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="font-display font-bold text-2xl text-white">{token.symbol}</h1>
            <span className="text-bnb-muted">{token.name}</span>
            {token.is_runner && (
              <span className="inline-flex items-center gap-1 rounded-full bg-bnb-yellow px-2 py-0.5 text-[10px] font-bold text-bnb-black">
                <Flame size={11} /> RUNNER
              </span>
            )}
          </div>
          <div className="mt-1 flex items-center gap-2 flex-wrap text-xs text-bnb-muted font-mono">
            <span>{shortAddress(token.address, 6)}</span>
            <span>· {formatAge(token.creation_timestamp)} old</span>
            <span>· {token.bonding_platform || token.dex || "unknown platform"}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <CopyButton value={token.address} label="Copy CA" />
          <BookmarkButton address={token.address} />
          <a
            href={bscScanUrl(token.address)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-md border border-bnb-border bg-bnb-panel px-2.5 py-1.5 text-xs text-bnb-muted hover:text-bnb-yellow hover:border-bnb-yellow/40 min-h-[36px]"
          >
            BscScan <ExternalLink size={12} />
          </a>
        </div>
      </div>

      <div className="rounded-xl border border-bnb-border bg-bnb-panel/60 p-4">
        <BondingProgressBar progress={token.bonding_progress} isBonding={token.is_bonding} platform={token.bonding_platform || token.dex} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <Metric label="Price" value={`$${token.price_usd.toPrecision(4)}`} />
        <Metric label="Market Cap" value={formatUsd(token.market_cap_usd)} />
        <Metric label="Liquidity" value={formatUsd(token.liquidity_usd)} />
        <Metric label="Volume 24h" value={formatUsd(token.volume_24h_usd)} />
        <Metric label="Holders" value={String(token.holder_count)} />
        <Metric label="Runner Score" value={`${token.runner_score.toFixed(0)}/100`} accent />
        <Metric label="Buy / Sell Tax" value={`${token.buy_tax_pct.toFixed(1)}% / ${token.sell_tax_pct.toFixed(1)}%`} />
        <Metric label="Top 10 Holders" value={`${token.top10_holder_pct.toFixed(1)}%`} />
      </div>

      <div className="flex items-center gap-2">
        <SecurityBadge score={token.security_score} honeypot={token.honeypot_risk} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SecurityChecklist token={token} />
        <TokenChart token={token} />
      </div>
    </div>
  );
}

function Metric({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-xl border border-bnb-border bg-bnb-panel/60 px-3 py-2.5">
      <div className="text-[10px] uppercase tracking-wide text-bnb-muted">{label}</div>
      <div className={`font-mono font-bold tabular text-lg ${accent ? "text-bnb-yellow" : "text-white"}`}>{value}</div>
    </div>
  );
}
