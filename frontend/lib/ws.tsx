"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { api } from "./api";
import type { Token, WsEvent } from "./types";

/**
 * Was a real WebSocket connection to a FastAPI backend; that backend no
 * longer runs anywhere (see the $0/month rework — the scanner is now a
 * scheduled GitHub Actions job, not an always-on server that could hold
 * a socket open). This keeps the exact same `useTokenStream()` interface
 * (`connected`, `subscribe`) so every consumer (Header's LIVE indicator,
 * LiveFeed's refetch-on-event) is unchanged — internally it's now a poll
 * loop that diffs each response against the previous one and synthesizes
 * the same event types a real socket would have pushed.
 *
 * Honest trade-off: this is "new data shows up within ~15-20s", not
 * instant. Combined with the scanner's own ~15s poll cadence, worst-case
 * end-to-end latency from on-chain event to your screen is roughly 30-40s.
 */
const POLL_INTERVAL_MS = 15_000;

type Listener = (event: WsEvent) => void;

interface WsContextValue {
  connected: boolean;
  subscribe: (listener: Listener) => () => void;
}

const WsContext = createContext<WsContextValue>({
  connected: false,
  subscribe: () => () => {},
});

export function useTokenStream() {
  return useContext(WsContext);
}

export function WsProvider({ children }: { children: React.ReactNode }) {
  const [connected, setConnected] = useState(false);
  const listeners = useRef<Set<Listener>>(new Set());
  const known = useRef<Map<string, Token> | null>(null); // null = not yet seeded

  const subscribe = useCallback((listener: Listener) => {
    listeners.current.add(listener);
    return () => listeners.current.delete(listener);
  }, []);

  const emit = useCallback((event: WsEvent) => {
    listeners.current.forEach((l) => l(event));

    if (event.type === "runner_flagged") {
      toast.success(`🚀 Runner: ${event.data.symbol} (${Math.round(event.data.runner_score)}/100)`, {
        style: { background: "#1E2329", color: "#F0B90B", border: "1px solid #2B3139" },
      });
    } else if (event.type === "new_token") {
      toast(`New token: ${event.data.symbol}`, {
        icon: "🆕",
        style: { background: "#1E2329", color: "#EAECEF", border: "1px solid #2B3139" },
      });
    } else if (event.type === "bonding_complete") {
      toast(`${event.data.symbol} finished bonding ✅`, {
        style: { background: "#1E2329", color: "#0ECB81", border: "1px solid #2B3139" },
      });
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const { items } = await api.listTokens({ limit: 200, sort_by: "created_at", order: "desc" });
        if (cancelled) return;
        setConnected(true);

        if (known.current === null) {
          // First poll after page load: seed the map silently so we don't
          // fire a "new token" toast for every token that already existed.
          known.current = new Map(items.map((t) => [t.address, t]));
        } else {
          for (const token of items) {
            const prev = known.current.get(token.address);
            if (!prev) {
              emit({ type: "new_token", data: token });
            } else if (token.is_runner && !prev.is_runner) {
              emit({ type: "runner_flagged", data: token });
            } else if (!token.is_bonding && prev.is_bonding) {
              emit({ type: "bonding_complete", data: token });
            } else if (token.last_checked_at !== prev.last_checked_at) {
              emit({ type: "token_updated", data: token });
            }
            known.current.set(token.address, token);
          }
        }
      } catch {
        if (!cancelled) setConnected(false);
      }
    }

    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [emit]);

  return <WsContext.Provider value={{ connected, subscribe }}>{children}</WsContext.Provider>;
}
