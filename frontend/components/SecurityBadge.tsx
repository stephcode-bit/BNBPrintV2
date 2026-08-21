import { ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import clsx from "clsx";
import { securityTier } from "@/lib/utils";

export default function SecurityBadge({
  score,
  honeypot,
  size = "md",
}: {
  score: number;
  honeypot?: boolean | null;
  size?: "sm" | "md";
}) {
  const tier = honeypot ? "danger" : securityTier(score);

  const config = {
    safe: {
      icon: ShieldCheck,
      classes: "border-bnb-green/40 bg-bnb-green/10 text-bnb-green",
      label: "Safer",
    },
    caution: {
      icon: ShieldQuestion,
      classes: "border-bnb-yellow/40 bg-bnb-yellow/10 text-bnb-yellow",
      label: "Caution",
    },
    danger: {
      icon: ShieldAlert,
      classes: "border-bnb-red/40 bg-bnb-red/10 text-bnb-red",
      label: honeypot ? "Honeypot" : "High risk",
    },
  }[tier];

  const Icon = config.icon;

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full border font-mono font-semibold",
        config.classes,
        size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-xs"
      )}
      title={`Security score ${score.toFixed(0)}/100`}
    >
      <Icon size={size === "sm" ? 11 : 13} />
      {config.label} · {score.toFixed(0)}
    </span>
  );
}
