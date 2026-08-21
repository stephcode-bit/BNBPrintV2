import Logo from "@/components/Logo";
import NotificationsToggle from "@/components/NotificationsToggle";

export default function AboutPage() {
  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Logo size={40} />
        <div>
          <h1 className="font-display font-bold text-2xl text-white">About BNBPRINT</h1>
          <p className="text-xs text-bnb-muted">BNB Chain Runner Radar</p>
        </div>
      </div>

      <Section title="What it does">
        BNBPRINT watches BNB Chain in real time for newly created tokens — especially ones launching on
        bonding-curve platforms like four.meme and GraFun — and screens each one for the warning signs of
        honeypots, rug pulls, and unlocked or wafer-thin liquidity. Tokens that clear the security bar and
        show real early momentum get flagged as potential runners before their curve finishes bonding.
      </Section>

      <Section title="How scoring works">
        Every token gets two scores. The <strong className="text-white">security score</strong> combines
        Ave AI's honeypot/rug analysis with our own on-chain checks — liquidity lock status, renounced
        ownership, mint controls, and holder concentration. The{" "}
        <strong className="text-white">runner score</strong> layers in momentum signals — buy volume
        relative to liquidity, holder growth rate, bonding speed, and market-cap sanity — but is capped hard
        if the security score is too low, so hype never overrides safety in the flagging logic.
      </Section>

      <Section title="Using it safely">
        Bonding-curve tokens are among the highest-risk assets in crypto: most go to zero, and even
        passing every automated check is not a guarantee of safety. BNBPRINT is a research and monitoring
        tool, not financial advice — always verify a contract yourself on BscScan, check the liquidity lock
        directly, and never risk more than you can afford to lose.
      </Section>

      <Section title="Install it">
        BNBPRINT is a Progressive Web App — install it from your browser's menu (or the install prompt) for
        a full-screen, app-like experience with offline access to your last-loaded feed and optional push
        notifications for new runners.
      </Section>

      <div className="rounded-xl border border-bnb-border bg-bnb-panel/50 p-5 flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
        <div>
          <h2 className="font-display font-semibold text-white mb-1">Push alerts</h2>
          <p className="text-sm text-bnb-muted">Get notified the moment a token is flagged as a likely runner — even when the app isn't open.</p>
        </div>
        <NotificationsToggle />
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-bnb-border bg-bnb-panel/50 p-5">
      <h2 className="font-display font-semibold text-white mb-2">{title}</h2>
      <p className="text-sm text-bnb-muted leading-relaxed">{children}</p>
    </div>
  );
}
