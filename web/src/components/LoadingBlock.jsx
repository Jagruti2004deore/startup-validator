export function LoadingBlock({ blocks = 3 }) {
  return (
    <div className="animate-pulse space-y-3" aria-busy="true" aria-label="Loading">
      <div className="h-6 w-1/3 rounded bg-stone-200" />
      {Array.from({ length: blocks }, (_, i) => (
        <div key={i} className="h-24 rounded-2xl bg-stone-100" />
      ))}
    </div>
  );
}