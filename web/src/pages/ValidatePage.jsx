import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { api } from "../api/client";
import { AccessCodePrompt } from "../components/AccessCodePrompt";
import { RunProgress } from "../components/RunProgress";
import { Button, Card, Notice } from "../components/ui";
import { friendlyError } from "../lib/errors";

const ACTIVE_RUN_KEY = "sv_active_run";
const MIN_LENGTH = 15;
const MAX_LENGTH = 1500;

export default function ValidatePage() {
  const navigate = useNavigate();
  const [idea, setIdea] = useState("");
  const [runId, setRunId] = useState(() => localStorage.getItem(ACTIVE_RUN_KEY));
  const [attempt, setAttempt] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const ready = idea.trim().length >= MIN_LENGTH;

  async function submit() {
    if (!ready || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const { run_id } = await api.startValidation(idea.trim());
      localStorage.setItem(ACTIVE_RUN_KEY, run_id);
      setRunId(run_id);
    } catch (e) {
      setError(friendlyError(e));
    } finally {
      setSubmitting(false);
    }
  }

  function reset() {
    localStorage.removeItem(ACTIVE_RUN_KEY);
    setRunId(null);
    setError(null);
  }

  function finish(id) {
    localStorage.removeItem(ACTIVE_RUN_KEY);
    setRunId(null);
    navigate(`/validations/${id}`);
  }

  if (runId) {
    return (
      <RunProgress
        key={`${runId}-${attempt}`}
        runId={runId}
        onDone={finish}
        onReset={reset}
        onAccessSaved={() => setAttempt((n) => n + 1)}
      />
    );
  }

  return (
    <div className="animate-fade-up">
      <header className="max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">Startup Validator</h1>
        <p className="mt-3 text-lg">Validate your idea before you build it.</p>
        <p className="mt-2 text-muted">
          Research the market, understand the competition, and make a decision based on evidence.
        </p>
      </header>

      <Card className="mt-8 max-w-3xl p-5 md:p-6">
        <label htmlFor="idea" className="block text-sm font-medium">
          What&apos;s your startup idea?
        </label>
        <textarea
          id="idea"
          value={idea}
          maxLength={MAX_LENGTH}
          rows={6}
          onChange={(event) => setIdea(event.target.value)}
          onKeyDown={(event) => {
            if ((event.ctrlKey || event.metaKey) && event.key === "Enter") submit();
          }}
          placeholder="e.g. An app that helps small businesses find and book available meeting rooms nearby with an approval workflow."
          className="mt-3 w-full resize-y rounded-xl border border-line bg-white px-4 py-3 text-[15px] leading-relaxed outline-none transition-colors placeholder:text-stone-400 focus:border-accent"
        />
        <div className="mt-2 flex items-center justify-between text-xs text-muted">
          <span>Describe the problem, target users, and solution if you know them.</span>
          <span className="tabular-nums">
            {idea.length}/{MAX_LENGTH}
          </span>
        </div>

        <div className="mt-5">
          <Button onClick={submit} disabled={!ready || submitting}>
            {submitting ? "Starting..." : "Validate Idea"}
            {!submitting && <ArrowRight className="h-4 w-4" />}
          </Button>
        </div>
      </Card>

      <div className="mt-5 max-w-3xl">
        {error?.needsAccessCode ? (
          <AccessCodePrompt
            onSaved={() => {
              setError(null);
              submit();
            }}
          />
        ) : (
          error && <Notice title={error.title}>{error.message}</Notice>
        )}
      </div>
    </div>
  );
}