import { NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

export async function GET() {
  const redis = getRedis();
  if (!redis) {
    return NextResponse.json(
      { error: "UPSTASH_REDIS_REST_URL/TOKEN not configured on this deployment" },
      { status: 503 }
    );
  }

  const stats = (await redis.get<Record<string, unknown>>("bnbprint:stats")) || {
    total_tokens: 0,
    bonding_tokens: 0,
    migrated_tokens: 0,
    runners_24h: 0,
    avg_security_score: 0,
    last_token_at: null,
  };

  return NextResponse.json(stats);
}
