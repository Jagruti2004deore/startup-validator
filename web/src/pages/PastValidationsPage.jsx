import { useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, History } from "lucide-react";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { ErrorPanel } from "../components/ErrorPanel";
import { LinkButton } from "../components/LinkButton";
import { LoadingBlock } from "../components/LoadingBlock";
import { VerdictBadge } from "../components/VerdictBadge";
import { useLoader } from "../hooks/useLoader";
import { friendlyLoadError } from "../lib/errors";
import { formatDate, truncate } from "../lib/format";
import { EVIDENCE_MAX } from "../lib/verdict";

const loadRuns = () => api.listRuns(50);

function StatusBadge({ run }) {
  if (run.status === "running") {
    return (
      <span className="rounded-full bg-accent-soft px-2.5 py-1 text-xs font-medium text-accent">
        In progress
      </span>
    );
  }
  if (run.status === "failed") {
    return (
      <span className="rounded-full bg-neutral-soft px-2.5 py-1 text-xs font-medium text-muted">
        Couldn&apos;t complete
      </span>
    );
  }
  return <VerdictBadge verdict={run.verdict} />;
}

function RunRow({ run }) {
  return (
    <Link
      to={`/validations/${run.id}`}
      className="group flex flex-col gap-3 rounded-2xl border border-line bg-white p-5 shadow-card transition-all hover:-translate-y-0.5 hover:border-stone-300 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="min-w-0">
        <p className="truncate font-medium">{run.title || truncate(run.idea_text, 60)}</p>
        <p className="mt-1 text-sm text-muted">{truncate(run.idea_text, 110)}</p>
      </div>
      <div className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-2 text-sm">
        <StatusBadge run={run} />
        {run.evidence_score != null && run.status === "done" && (
          <span className="tabular-nums text-muted">
            {run.evidence_score} / {EVIDENCE_MAX} evidence
          </span>
        )}
        <span className="text-muted">{formatDate(run.created_at)}</span>
        <ChevronRight className="hidden h-4 w-4 text-stone-400 transition-transform group-hover:translate-x-0.5 sm:block" />
      </div>
    </Link>
  );
}

export default function PastValidationsPage() {
  const [attempt, setAttempt] = useState(0);
  const state = useLoader(loadRuns, attempt);
  const retry = () => setAttempt((n) => n + 1);

  return (
    <div className="animate-fade-up max-w-3xl">
      <h1 className="text-2xl font-semibold tracking-tight">Past Validations</h1>
      <p className="mt-1 text-muted">Review your previous startup ideas and validation results.</p>

      <div className="mt-8">
        {state.phase === "loading" && <LoadingBlock blocks={3} />}
        {state.phase === "error" && (
          <ErrorPanel error={friendlyLoadError(state.error)} onRetry={retry} />
        )}
        {state.phase === "ready" && state.data.length === 0 && (
          <EmptyState
            icon={History}
            title="No validations yet."
            text="Your analyzed startup ideas will appear here."
            action={<LinkButton to="/">Validate your first idea →</LinkButton>}
          />
        )}
        {state.phase === "ready" && state.data.length > 0 && (
          <div className="space-y-3">
            {state.data.map((run) => (
              <RunRow key={run.id} run={run} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}