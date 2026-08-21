"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { Radar } from "lucide-react";
import { api } from "@/lib/api";
import type { TokenFilters } from "@/lib/types";
import { useTokenStream } from "@/lib/ws";
import TokenCard from "./TokenCard";
import TokenCardSkeleton from "./TokenCardSkeleton";

export default function LiveFeed({ filters }: { filters: TokenFilters }) {
  const queryClient = useQueryClient();
  const { subscribe } = useTokenStream();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const queryKey = ["tokens", filters];

  const { data, isLoading, isError } = useQuery({
    queryKey,
    queryFn: () => api.listTokens(filters),
    refetchInterval: 45_000,
  });

  useEffect(() => {
    return subscribe(() => {
      // Live events can arrive in bursts (a handful of new tokens back to
      // back); debounce so we don't hammer the API with a refetch per event.
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["tokens"] });
      }, 1200);
    });
  }, [subscribe, queryClient]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <TokenCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-bnb-red/30 bg-bnb-red/5 p-8 text-center text-sm text-bnb-red">
        Couldn't reach the token feed. Check that <code className="font-mono">UPSTASH_REDIS_REST_URL</code> and{" "}
        <code className="font-mono">UPSTASH_REDIS_REST_TOKEN</code> are set on this deployment.
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-bnb-border p-12 text-center">
        <Radar className="mx-auto mb-3 text-bnb-muted" size={28} />
        <p className="text-sm text-bnb-muted">No tokens match these filters yet. Widen your filters, or wait — the radar is always scanning.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
      {data.items.map((token) => (
        <TokenCard key={token.address} token={token} />
      ))}
    </div>
  );
}
