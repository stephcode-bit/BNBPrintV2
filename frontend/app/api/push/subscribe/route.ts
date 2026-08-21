import { NextRequest, NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

/**
 * Writes into the same bnbprint:push_subs Redis hash the Python scanner
 * reads from (app/services/push_runner.py) — field = endpoint, value =
 * the subscription JSON, so HSET here is naturally an upsert/dedupe.
 */
export async function POST(req: NextRequest) {
  const redis = getRedis();
  if (!redis) {
    return NextResponse.json(
      { error: "UPSTASH_REDIS_REST_URL/TOKEN not configured on this deployment" },
      { status: 503 }
    );
  }

  const body = await req.json();
  const { user_id, endpoint, p256dh, auth } = body || {};
  if (!endpoint || !p256dh || !auth) {
    return NextResponse.json({ detail: "endpoint, p256dh, and auth are required" }, { status: 422 });
  }

  await redis.hset("bnbprint:push_subs", { [endpoint]: JSON.stringify({ user_id, endpoint, p256dh, auth }) });
  return NextResponse.json({ status: "subscribed" }, { status: 201 });
}
