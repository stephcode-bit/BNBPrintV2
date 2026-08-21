"use client";

import { Bell, BellRing } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { enablePushNotifications } from "@/lib/push";

export default function NotificationsToggle() {
  const [status, setStatus] = useState<"idle" | "enabled" | "loading">("idle");

  async function handleClick() {
    setStatus("loading");
    const result = await enablePushNotifications();
    if (result === "enabled") {
      setStatus("enabled");
      toast.success("Push alerts enabled — you'll get notified when a runner is flagged.");
    } else {
      setStatus("idle");
      const messages: Record<string, string> = {
        denied: "Notification permission was denied in your browser settings.",
        unsupported: "Push notifications aren't supported in this browser. Install the app first, or use in-app alerts.",
        unconfigured: "Push isn't configured on the backend yet (missing VAPID keys) — in-app alerts still work.",
      };
      toast(messages[result] || "Couldn't enable push notifications.");
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={status === "loading" || status === "enabled"}
      className="inline-flex items-center gap-2 rounded-lg border border-bnb-border bg-bnb-panel px-4 py-2.5 text-sm text-white hover:border-bnb-yellow/40 disabled:opacity-70 min-h-[44px]"
    >
      {status === "enabled" ? <BellRing size={16} className="text-bnb-yellow" /> : <Bell size={16} />}
      {status === "enabled" ? "Push alerts enabled" : status === "loading" ? "Requesting…" : "Enable push alerts"}
    </button>
  );
}
