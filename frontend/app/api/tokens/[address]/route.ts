import { NextResponse } from "next/server";
import { getRedis } from "@/lib/redis";

export const dynamic = "force-dynamic";

export async function GET(_req: Request, { params }: { params: { address: string } }) {
  const redis = getRedis();
  if (!redis) {
    return NextResponse.json(
      { error: "UPSTASH_REDIS_REST_URL/TOKEN not configured on this deployment" },
      { status: 503 }
    );
  }

  const raw = (await redis.get<any[]>("bnbprint:tokens")) || [];
  const token = raw.find((t) => t.address?.toLowerCase() === params.address.toLowerCase());

  if (!token) {
    return NextResponse.json({ detail: "Token not found" }, { status: 404 });
  }
  return NextResponse.json(token);
}
