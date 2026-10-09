export function EvidenceMeter({ value, max, barClass }) {
  return (
    <div
      className="flex items-center gap-1.5"
      role="img"
      aria-label={`${value} of ${max} evidence checks verified`}
    >
      {Array.from({ length: max }, (_, i) => (
        <span
          key={i}
          className={`h-1.5 w-6 rounded-full transition-colors ${i < value ? barClass : "bg-stone-200"}`}
        />
      ))}
    </div>
  );
}