"use client";

import clsx from "clsx";
import { Search, SlidersHorizontal } from "lucide-react";
import type { TokenFilters } from "@/lib/types";

const PLATFORMS = [
  { value: "", label: "All platforms" },
  { value: "four.meme", label: "four.meme" },
  { value: "grafun", label: "GraFun" },
  { value: "pancakeswap_v2", label: "PancakeSwap" },
];

const SORTS: { value: string; label: string }[] = [
  { value: "created_at", label: "Newest" },
  { value: "runner_score", label: "Runner score" },
  { value: "security_score", label: "Security score" },
  { value: "bonding_progress", label: "Bonding %" },
  { value: "volume_24h_usd", label: "Volume 24h" },
  { value: "liquidity_usd", label: "Liquidity" },
];

export default function FilterBar({
  filters,
  onChange,
}: {
  filters: TokenFilters;
  onChange: (next: TokenFilters) => void;
}) {
  function set<K extends keyof TokenFilters>(key: K, value: TokenFilters[K]) {
    onChange({ ...filters, [key]: value, offset: 0 });
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-bnb-border bg-bnb-panel/50 p-3">
      <div className="flex flex-col sm:flex-row gap-2.5">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-bnb-muted" />
          <input
            value={filters.search || ""}
            onChange={(e) => set("search", e.target.value)}
            placeholder="Search symbol, name, or contract address…"
            className="w-full rounded-lg border border-bnb-border bg-bnb-black/50 pl-9 pr-3 py-2.5 text-sm text-white placeholder:text-bnb-muted focus:border-bnb-yellow/50 outline-none"
          />
        </div>

        <select
          value={filters.platform || ""}
          onChange={(e) => set("platform", e.target.value || undefined)}
          className="rounded-lg border border-bnb-border bg-bnb-black/50 px-3 py-2.5 text-sm text-white focus:border-bnb-yellow/50 outline-none min-h-[44px]"
        >
          {PLATFORMS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>

        <select
          value={filters.sort_by || "created_at"}
          onChange={(e) => set("sort_by", e.target.value)}
          className="rounded-lg border border-bnb-border bg-bnb-black/50 px-3 py-2.5 text-sm text-white focus:border-bnb-yellow/50 outline-none min-h-[44px]"
        >
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              Sort: {s.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <SlidersHorizontal size={14} className="text-bnb-muted mr-0.5" />

        <Toggle
          active={filters.bonding === true}
          onClick={() => set("bonding", filters.bonding === true ? undefined : true)}
          label="Still bonding"
        />
        <Toggle
          active={filters.bonding === false}
          onClick={() => set("bonding", filters.bonding === false ? undefined : false)}
          label="Migrated"
        />
        <Toggle
          active={!!filters.runners_only}
          onClick={() => set("runners_only", !filters.runners_only)}
          label="🔥 Runners only"
        />
        <Toggle
          active={filters.min_security_score === 70}
          onClick={() => set("min_security_score", filters.min_security_score === 70 ? undefined : 70)}
          label="Security ≥ 70"
        />

        <div className="ml-auto flex items-center rounded-lg border border-bnb-border overflow-hidden">
          <button
            type="button"
            onClick={() => set("order", "desc")}
            className={clsx(
              "px-2.5 py-1.5 text-xs font-mono",
              filters.order !== "asc" ? "bg-bnb-yellow/10 text-bnb-yellow" : "text-bnb-muted"
            )}
          >
            DESC
          </button>
          <button
            type="button"
            onClick={() => set("order", "asc")}
            className={clsx(
              "px-2.5 py-1.5 text-xs font-mono",
              filters.order === "asc" ? "bg-bnb-yellow/10 text-bnb-yellow" : "text-bnb-muted"
            )}
          >
            ASC
          </button>
        </div>
      </div>
    </div>
  );
}

function Toggle({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors min-h-[36px]",
        active
          ? "border-bnb-yellow bg-bnb-yellow/15 text-bnb-yellow"
          : "border-bnb-border text-bnb-muted hover:text-white hover:border-white/30"
      )}
    >
      {label}
    </button>
  );
}
