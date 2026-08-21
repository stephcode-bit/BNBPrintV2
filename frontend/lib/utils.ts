import { formatDistanceToNowStrict } from "date-fns";

export function shortAddress(address: string, chars = 4): string {
  if (!address) return "";
  return `${address.slice(0, 2 + chars)}…${address.slice(-chars)}`;
}

export function formatUsd(value: number): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "$0";
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  if (value >= 1) return `$${value.toFixed(2)}`;
  return `$${value.toPrecision(3)}`;
}

export function formatCompact(value: number): string {
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(
    value ?? 0
  );
}

export function formatAge(iso: string): string {
  try {
    return formatDistanceToNowStrict(new Date(iso), { addSuffix: false });
  } catch {
    return "—";
  }
}

export function bscScanUrl(address: string): string {
  return `https://bscscan.com/token/${address}`;
}

export function clampPct(value: number): number {
  return Math.max(0, Math.min(100, value ?? 0));
}

export function securityTier(score: number): "safe" | "caution" | "danger" {
  if (score >= 70) return "safe";
  if (score >= 40) return "caution";
  return "danger";
}
