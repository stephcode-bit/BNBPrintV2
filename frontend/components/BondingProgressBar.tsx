import clsx from "clsx";
import { clampPct } from "@/lib/utils";

const SEGMENTS = 24;

export default function BondingProgressBar({
  progress,
  isBonding,
  platform,
  compact = false,
}: {
  progress: number;
  isBonding: boolean;
  platform?: string | null;
  compact?: boolean;
}) {
  const pct = clampPct(progress);
  const filledSegments = Math.round((pct / 100) * SEGMENTS);
  const migrated = !isBonding || pct >= 100;

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] uppercase tracking-wider text-bnb-muted font-mono">
          {platform ? platform.replace(/\.meme$/, ".meme").toUpperCase() : "BONDING"}
        </span>
        <span
          className={clsx(
            "text-[10px] font-mono font-bold tabular",
            migrated ? "text-bnb-green" : "text-bnb-yellow"
          )}
        >
          {migrated ? "MIGRATED ✓" : `${pct.toFixed(1)}%`}
        </span>
      </div>
      <div className={clsx("relative flex gap-[2px] rounded-sm overflow-hidden", compact ? "h-2" : "h-2.5")}>
        {Array.from({ length: SEGMENTS }).map((_, i) => {
          const filled = i < filledSegments;
          return (
            <div
              key={i}
              className={clsx(
                "flex-1 rounded-[1px] transition-colors duration-300",
                filled ? (migrated ? "bg-bnb-green" : "bg-bnb-yellow") : "bg-bnb-border"
              )}
            />
          );
        })}
        {!migrated && pct > 2 && (
          <div className="meter-sheen absolute inset-0 pointer-events-none overflow-hidden" />
        )}
      </div>
    </div>
  );
}
