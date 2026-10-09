import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { ApiError } from "../lib/errors";

/** Loads the finished report and the research log of one validation. */
export function useReport(runId) {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState(null);
  const key = `${runId}:${attempt}`;

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getReport(runId), api.getRun(runId)])
      .then(([report, run]) => {
        if (!cancelled) setResult({ key, phase: "ready", report, events: run.events });
      })
      .catch((error) => {
        if (cancelled) return;
        const stillRunning = error instanceof ApiError && error.status === 409;
        setResult({ key, phase: stillRunning ? "running" : "error", error });
      });
    return () => {
      cancelled = true;
    };
  }, [runId, key]);

  // A result that belongs to an older run or attempt counts as "still loading".
  const current = result && result.key === key ? result : { phase: "loading" };
  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  return { ...current, retry };
}