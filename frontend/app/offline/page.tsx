import Logo from "@/components/Logo";

export default function OfflinePage() {
  return (
    <div className="flex flex-col items-center justify-center text-center gap-4 py-24">
      <Logo size={48} />
      <h1 className="font-display font-bold text-xl text-white">You're offline</h1>
      <p className="text-sm text-bnb-muted max-w-sm">
        BNBPRINT can't reach the network right now. Reconnect to keep scanning for runners — previously
        loaded pages may still be available from cache.
      </p>
    </div>
  );
}
