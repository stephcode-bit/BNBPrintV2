"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, Flame, GaugeCircle, Radar, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { formatCompact } from "@/lib/utils";

export default function StatsBar() {
  const { data, isLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: api.getStats,
    refetchInterval: 20_000,
  });

  const tiles = [
    { label: "Tracked Tokens", value: data ? formatCompact(data.total_tokens) : "—", icon: Radar },
    { label: "Still Bonding", value: data ? formatCompact(data.bonding_tokens) : "—", icon: GaugeCircle },
    { label: "Migrated", value: data ? formatCompact(data.migrated_tokens) : "—", icon: Activity },
    { label: "Runners (24h)", value: data ? formatCompact(data.runners_24h) : "—", icon: Flame, accent: true },
    { label: "Avg Security", value: data ? `${data.avg_security_score.toFixed(0)}/100` : "—", icon: ShieldCheck },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
      {tiles.map((tile) => (
        <div
          key={tile.label}
          className="rounded-xl border border-bnb-border bg-bnb-panel/60 px-3.5 py-3 flex items-center gap-3"
        >
          <tile.icon size={18} className={tile.accent ? "text-bnb-yellow" : "text-bnb-muted"} />
          <div className="min-w-0">
            <div className="text-[10px] uppercase tracking-wide text-bnb-muted truncate">{tile.label}</div>
            <div
              className={`font-mono font-bold text-lg tabular ${
                tile.accent ? "text-bnb-yellow" : "text-white"
              } ${isLoading ? "animate-pulse" : ""}`}
            >
              {tile.value}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
