import Link from "next/link";
import clsx from "clsx";
import { Flame, Lock, LockOpen, Users } from "lucide-react";
import type { Token } from "@/lib/types";
import { formatAge, formatUsd, shortAddress } from "@/lib/utils";
import CopyButton from "./CopyButton";
import BookmarkButton from "./BookmarkButton";
import SecurityBadge from "./SecurityBadge";
import BondingProgressBar from "./BondingProgressBar";

export default function TokenCard({ token, highlight = false }: { token: Token; highlight?: boolean }) {
  return (
    <Link
      href={`/token/${token.address}`}
      className={clsx(
        "group relative block rounded-xl border bg-bnb-panel/70 p-4 transition-all hover:-translate-y-0.5 hover:shadow-glow animate-fade-up",
        token.is_runner ? "border-bnb-yellow/50" : "border-bnb-border hover:border-bnb-yellow/30",
        highlight && "ring-1 ring-bnb-yellow/40"
      )}
    >
      {token.is_runner && (
        <div className="absolute -top-2.5 left-4 flex items-center gap-1 rounded-full bg-bnb-yellow px-2 py-0.5 text-[10px] font-bold text-bnb-black shadow-glow">
          <Flame size={11} /> RUNNER {token.runner_score.toFixed(0)}
        </div>
      )}

      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-display font-bold text-base text-white truncate">{token.symbol}</h3>
            <span className="text-xs text-bnb-muted truncate">{token.name}</span>
          </div>
          <div className="mt-0.5 flex items-center gap-1.5 text-xs text-bnb-muted font-mono">
            <span>{shortAddress(token.address)}</span>
            <span className="text-bnb-border">•</span>
            <span>{formatAge(token.creation_timestamp)} old</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <BookmarkButton address={token.address} />
          <CopyButton value={token.address} label="" className="w-9 h-9 p-0" />
        </div>
      </div>

      <div className="mt-3">
        <BondingProgressBar
          progress={token.bonding_progress}
          isBonding={token.is_bonding}
          platform={token.bonding_platform || token.dex}
        />
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
        <Metric label="Market Cap" value={formatUsd(token.market_cap_usd)} />
        <Metric label="Liquidity" value={formatUsd(token.liquidity_usd)} />
        <Metric label="Vol 24h" value={formatUsd(token.volume_24h_usd)} />
      </div>

      <div className="mt-3 flex items-center justify-between">
        <SecurityBadge score={token.security_score} honeypot={token.honeypot_risk} size="sm" />
        <div className="flex items-center gap-2 text-[11px] text-bnb-muted">
          <span className="inline-flex items-center gap-1" title="Holders">
            <Users size={12} /> {token.holder_count}
          </span>
          <span className="inline-flex items-center gap-1" title={token.liquidity_locked ? "Liquidity locked" : "Liquidity not locked"}>
            {token.liquidity_locked ? <Lock size={12} className="text-bnb-green" /> : <LockOpen size={12} className="text-bnb-red" />}
          </span>
        </div>
      </div>
    </Link>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-bnb-black/40 px-2 py-1.5 border border-bnb-border/50">
      <div className="text-[9px] uppercase tracking-wide text-bnb-muted">{label}</div>
      <div className="font-mono font-semibold tabular text-white">{value}</div>
    </div>
  );
}
