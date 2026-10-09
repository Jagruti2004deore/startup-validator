import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { useRunProgress } from "../hooks/useRunProgress";
import { failedRunMessage, friendlyError } from "../lib/errors";
import { STAGES, isDiggingDeeper, stageStates } from "../lib/progress";
import { AccessCodePrompt } from "./AccessCodePrompt";
import { Button, Card, Notice } from "./ui";

function useElapsed(active) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!active) return undefined;
    const id = window.setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => window.clearInterval(id);
  }, [active]);
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

function StageIcon({ state }) {
  if (state === "done") {
    return <Check className="h-5 w-5 shrink-0 rounded-full bg-good-soft p-1 text-good" />;
  }
  if (state === "active") {
    return (
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-accent">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
      </span>
    );
  }
  return <span className="h-5 w-5 shrink-0 rounded-full border border-line" />;
}

export function RunProgress({ runId, onDone, onReset, onAccessSaved }) {
  const { events, status, idea, error } = useRunProgress(runId);
  const elapsed = useElapsed(status === "running" && !error);

  useEffect(() => {
    if (status === "done") onDone(runId);
  }, [status, runId, onDone]);

  if (error) {
    const friendly = friendlyError(error);
    if (friendly.needsAccessCode) return <AccessCodePrompt onSaved={onAccessSaved} />;
    return (
      <Notice
        title={friendly.title}
        action={<Button variant="secondary" onClick={onReset}>Try again</Button>}
      >
        {friendly.message}
      </Notice>
    );
  }

  if (status === "failed") {
    const friendly = failedRunMessage(events);
    return (
      <Notice
        title={friendly.title}
        action={<Button variant="secondary" onClick={onReset}>Try again</Button>}
      >
        {friendly.message}
      </Notice>
    );
  }

  const nodes = events.map((e) => e.node);
  const states = stageStates(nodes, status);
  const digging = isDiggingDeeper(nodes);

  return (
    <Card className="animate-fade-up max-w-3xl p-6 md:p-8">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold tracking-tight">Analyzing your idea...</h2>
          {idea && <p className="mt-1 line-clamp-2 text-sm text-muted">{idea}</p>}
        </div>
        <span className="shrink-0 text-sm tabular-nums text-muted">{elapsed}</span>
      </div>

      <ul className="mt-6 divide-y divide-line/60">
        {STAGES.map((label, i) => (
          <li key={label} className="flex items-center gap-3 py-3">
            <StageIcon state={states[i]} />
            <span className={states[i] === "waiting" ? "text-muted" : "text-ink"}>{label}</span>
            {states[i] === "active" && digging && (
              <span className="ml-auto hidden text-xs text-muted sm:inline">
                Digging deeper into gaps in the evidence
              </span>
            )}
          </li>
        ))}
      </ul>

      <p className="mt-5 text-xs text-muted">
        Careful research takes a few minutes. You can leave this page open or come back later.
      </p>
    </Card>
  );
}