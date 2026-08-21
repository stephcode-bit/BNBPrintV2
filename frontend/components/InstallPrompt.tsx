"use client";

import { Download, X } from "lucide-react";
import { useEffect, useState } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

export default function InstallPrompt() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (localStorage.getItem("bnbprint_install_dismissed") === "1") setDismissed(true);

    function handler(e: Event) {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
    }
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  if (!deferred || dismissed) return null;

  async function install() {
    if (!deferred) return;
    await deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
  }

  function dismiss() {
    setDismissed(true);
    localStorage.setItem("bnbprint_install_dismissed", "1");
  }

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 rounded-xl border border-bnb-yellow/40 bg-bnb-panel px-4 py-3 shadow-glow animate-fade-up">
      <Download size={16} className="text-bnb-yellow shrink-0" />
      <p className="text-xs text-white">
        Install <span className="font-semibold text-bnb-yellow">BNBPRINT</span> for one-tap access and push alerts.
      </p>
      <button
        onClick={install}
        className="rounded-md bg-bnb-yellow px-3 py-1.5 text-xs font-bold text-bnb-black hover:brightness-110"
      >
        Install
      </button>
      <button onClick={dismiss} aria-label="Dismiss" className="text-bnb-muted hover:text-white p-1">
        <X size={14} />
      </button>
    </div>
  );
}
