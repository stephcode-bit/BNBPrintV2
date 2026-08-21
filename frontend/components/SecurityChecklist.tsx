import { AlertTriangle, Check, HelpCircle, X } from "lucide-react";
import clsx from "clsx";
import type { Token } from "@/lib/types";

type CheckState = "pass" | "fail" | "warn" | "unknown";

function Row({ label, state, detail }: { label: string; state: CheckState; detail?: string }) {
  const config: Record<CheckState, { icon: typeof Check; classes: string }> = {
    pass: { icon: Check, classes: "text-bnb-green" },
    fail: { icon: X, classes: "text-bnb-red" },
    warn: { icon: AlertTriangle, classes: "text-bnb-yellow" },
    unknown: { icon: HelpCircle, classes: "text-bnb-muted" },
  };
  const { icon: Icon, classes } = config[state];

  return (
    <div className="flex items-center justify-between py-2.5 border-b border-bnb-border/50 last:border-0">
      <span className="text-sm text-white/90">{label}</span>
      <span className={clsx("flex items-center gap-1.5 text-xs font-mono", classes)}>
        {detail}
        <Icon size={15} />
      </span>
    </div>
  );
}

export default function SecurityChecklist({ token }: { token: Token }) {
  const totalTax = (token.buy_tax_pct || 0) + (token.sell_tax_pct || 0);

  return (
    <div className="rounded-xl border border-bnb-border bg-bnb-panel/60 p-4">
      <h3 className="font-display font-semibold text-sm text-white mb-1">Security Breakdown</h3>
      <p className="text-xs text-bnb-muted mb-2">
        Combines Ave AI's scoring with our own on-chain checks. Always verify independently before trading.
      </p>
      <Row
        label="Honeypot simulation"
        state={token.honeypot_risk === true ? "fail" : token.honeypot_risk === false ? "pass" : "unknown"}
        detail={token.honeypot_risk === null ? "not checked" : undefined}
      />
      <Row label="Liquidity locked" state={token.liquidity_locked ? "pass" : "fail"} />
      <Row label="Owner renounced" state={token.owner_renounced ? "pass" : "warn"} />
      <Row label="Mint disabled" state={token.mint_disabled ? "pass" : "warn"} />
      <Row label="Contract verified" state={token.contract_verified ? "pass" : "unknown"} />
      <Row
        label="Top 10 holder concentration"
        state={token.top10_holder_pct > 60 ? "fail" : token.top10_holder_pct > 35 ? "warn" : "pass"}
        detail={`${token.top10_holder_pct.toFixed(1)}%`}
      />
      <Row
        label="Buy/sell tax"
        state={totalTax > 20 ? "fail" : totalTax > 10 ? "warn" : "pass"}
        detail={`${token.buy_tax_pct.toFixed(1)}% / ${token.sell_tax_pct.toFixed(1)}%`}
      />
      {token.ave_security_score !== null && (
        <Row label="Ave AI security score" state="unknown" detail={`${token.ave_security_score.toFixed(0)}/100`} />
      )}
    </div>
  );
}
