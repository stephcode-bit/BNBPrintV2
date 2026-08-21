export default function TokenCardSkeleton() {
  return (
    <div className="rounded-xl border border-bnb-border bg-bnb-panel/50 p-4 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-4 w-24 rounded bg-bnb-border" />
        <div className="h-8 w-16 rounded bg-bnb-border" />
      </div>
      <div className="mt-3 h-2.5 w-full rounded bg-bnb-border" />
      <div className="mt-3 grid grid-cols-3 gap-2">
        <div className="h-10 rounded bg-bnb-border" />
        <div className="h-10 rounded bg-bnb-border" />
        <div className="h-10 rounded bg-bnb-border" />
      </div>
      <div className="mt-3 h-5 w-20 rounded-full bg-bnb-border" />
    </div>
  );
}
