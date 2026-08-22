import { NextRequest, NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic"; // always read the latest snapshot, never cache at the edge

type SortKey =
  | "created_at"
  | "security_score"
  | "runner_score"
  | "bonding_progress"
  | "volume_24h_usd"
  | "liquidity_usd"
  | "market_cap_usd";

/**
 * Reads the token snapshot the scanner writes to Upstash (bnbprint:tokens
 * — see backend/app/services/store.py) and applies the same filter/sort/
 * paginate logic the old FastAPI /api/tokens endpoint had, just in JS
 * instead of SQL, since there's no database to push the WHERE clause to
 * anymore — the whole snapshot is small enough (capped at 300 tokens) that
 * filtering in memory on every request is genuinely fine at this scale.
 */
export async function GET(req: NextRequest) {
  const redis = getRedis();
  if (!redis) {
    return NextResponse.json(
      { error: "UPSTASH_REDIS_REST_URL/TOKEN not configured on this deployment" },
      { status: 503 }
    );
  }

  const raw = (await redis.get<any[]>("bnbprint:tokens")) || [];
  const params = req.nextUrl.searchParams;

  const bonding = params.get("bonding");
  const platform = params.get("platform");
  const minSecurity = params.get("min_security_score");
  const runnersOnly = params.get("runners_only") === "true";
  const search = params.get("search")?.toLowerCase();
  const sortBy = (params.get("sort_by") as SortKey) || "created_at";
  const order = params.get("order") === "asc" ? "asc" : "desc";
  const limit = Math.min(200, Math.max(1, Number(params.get("limit")) || 50));
  const offset = Math.max(0, Number(params.get("offset")) || 0);

  let items = raw;
  if (bonding !== null) items = items.filter((t) => t.is_bonding === (bonding === "true"));
  if (platform) items = items.filter((t) => t.bonding_platform === platform);
  if (minSecurity) items = items.filter((t) => (t.security_score ?? 0) >= Number(minSecurity));
  if (runnersOnly) items = items.filter((t) => t.is_runner);
  if (search) {
    items = items.filter(
      (t) =>
        t.symbol?.toLowerCase().includes(search) ||
        t.name?.toLowerCase().includes(search) ||
        t.address?.toLowerCase().includes(search)
    );
  }

  // Token records never actually carry a "created_at" field (that was a
  // legacy Postgres column) — only "creation_timestamp". Left unaliased,
  // sorting by the default "created_at" compared every token as equal
  // (undefined ?? 0 for both sides) and silently fell back to raw storage
  // order, which is oldest-first — the exact opposite of the "Newest"
  // sort the UI claims to apply, and why long-dead tokens were showing up
  // at the top of the default view.
  const effectiveSortBy = sortBy === "created_at" ? "creation_timestamp" : sortBy;

  items = [...items].sort((a, b) => {
    const av = a[effectiveSortBy] ?? 0;
    const bv = b[effectiveSortBy] ?? 0;
    const cmp = typeof av === "string" ? av.localeCompare(bv) : av - bv;
    return order === "desc" ? -cmp : cmp;
  });

  const total = items.length;
  const page = items.slice(offset, offset + limit);

  return NextResponse.json({ items: page, total, limit, offset });
}
