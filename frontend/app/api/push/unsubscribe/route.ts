import { NextRequest, NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

export async function DELETE(req: NextRequest) {
  const redis = getRedis();
  if (!redis) {
    return NextResponse.json(
      { error: "UPSTASH_REDIS_REST_URL/TOKEN not configured on this deployment" },
      { status: 503 }
    );
  }

  const endpoint = req.nextUrl.searchParams.get("endpoint");
  if (!endpoint) {
    return NextResponse.json({ detail: "endpoint query param is required" }, { status: 422 });
  }

  await redis.hdel("bnbprint:push_subs", endpoint);
  return new NextResponse(null, { status: 204 });
}
