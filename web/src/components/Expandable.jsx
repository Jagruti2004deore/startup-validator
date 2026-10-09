import { useState } from "react";
import { ChevronRight } from "lucide-react";

export function Expandable({ summary, children, defaultOpen = false, className = "" }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={className}>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-start gap-3 text-left"
      >
        <ChevronRight
          className={`mt-1 h-4 w-4 shrink-0 text-muted transition-transform ${open ? "rotate-90" : ""}`}
        />
        <span className="min-w-0 flex-1">{summary}</span>
      </button>
      {open && <div className="animate-fade-up pl-7 pt-3">{children}</div>}
    </div>
  );
}