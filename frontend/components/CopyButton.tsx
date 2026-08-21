"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";

export default function CopyButton({
  value,
  label = "Copy CA",
  className,
}: {
  value: string;
  label?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
      } else {
        // Fallback for browsers/contexts without the async Clipboard API
        const el = document.createElement("textarea");
        el.value = value;
        el.style.position = "fixed";
        el.style.opacity = "0";
        document.body.appendChild(el);
        el.select();
        document.execCommand("copy");
        document.body.removeChild(el);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // clipboard blocked (permissions) — fail silently, button just won't flip to "copied"
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={label}
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs font-mono transition-all min-w-[44px] min-h-[36px] justify-center",
        copied
          ? "border-bnb-green/50 bg-bnb-green/10 text-bnb-green"
          : "border-bnb-border bg-bnb-panel text-bnb-muted hover:text-bnb-yellow hover:border-bnb-yellow/40",
        className
      )}
    >
      {copied ? <Check size={13} /> : <Copy size={13} />}
      {copied ? "Copied" : label}
    </button>
  );
}
