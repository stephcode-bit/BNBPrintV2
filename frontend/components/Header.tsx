"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import Logo from "./Logo";
import TickerTape from "./TickerTape";
import { useTokenStream } from "@/lib/ws";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/active", label: "Active" },
  { href: "/bookmarks", label: "Watchlist" },
  { href: "/about", label: "About" },
  { href: "/migrated", label: "Migrated" },
];

export default function Header() {
  const pathname = usePathname();
  const { connected } = useTokenStream();

  return (
    <header className="sticky top-0 z-40 backdrop-blur-md bg-bnb-black/85">
      <div className="w-full max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <Logo />
            <div className="leading-none">
              <span className="font-display font-bold text-lg tracking-tight text-white">
                BNB<span className="text-bnb-yellow">PRINT</span>
              </span>
              <div className="text-[10px] uppercase tracking-[0.2em] text-bnb-muted">Runner Radar</div>
            </div>
          </Link>

          <nav className="hidden sm:flex items-center gap-1">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "px-3.5 py-2 rounded-lg text-sm font-medium transition-colors",
                  pathname === item.href
                    ? "bg-bnb-yellow/10 text-bnb-yellow"
                    : "text-bnb-muted hover:text-white hover:bg-white/5"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <div
              className="hidden sm:flex items-center gap-1.5 rounded-full border border-bnb-border px-2.5 py-1 text-[11px] font-mono text-bnb-muted"
              title={connected ? "Live feed connected" : "Reconnecting…"}
            >
              <span
                className={clsx(
                  "h-1.5 w-1.5 rounded-full",
                  connected ? "bg-bnb-green shadow-[0_0_6px_#0ECB81]" : "bg-bnb-red animate-pulse"
                )}
              />
              {connected ? "LIVE" : "RECONNECTING"}
            </div>
          </div>
        </div>
      </div>
      <TickerTape />

      <nav className="sm:hidden flex items-center gap-1 px-4 pb-2 overflow-x-auto">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap",
              pathname === item.href ? "bg-bnb-yellow/10 text-bnb-yellow" : "text-bnb-muted"
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
