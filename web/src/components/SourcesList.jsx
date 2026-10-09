import { ArrowUpRight } from "lucide-react";

export function SourcesList({ sources }) {
  if (!sources.length) return <p className="text-sm text-muted">No sources were cited.</p>;
  return (
    <ol className="space-y-3">
      {sources.map((s) => (
        <li
          key={s.n}
          id={`source-${s.n}`}
          className="scroll-mt-28 rounded-xl border border-line bg-white p-4"
        >
          <div className="flex gap-3">
            <span className="mt-0.5 flex h-6 min-w-6 items-center justify-center rounded bg-stone-100 px-1.5 text-xs font-medium text-muted">
              {s.n}
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-medium">{s.title}</p>
              <p className="mt-0.5 text-xs text-muted">{s.domain}</p>
              {s.snippet && <p className="mt-2 text-sm text-muted">{s.snippet}</p>}
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-accent hover:underline"
              >
                Open source <ArrowUpRight className="h-4 w-4" />
              </a>
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}