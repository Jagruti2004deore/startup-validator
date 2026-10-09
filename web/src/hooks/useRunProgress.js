import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { ApiError } from "../lib/errors";

const POLL_MS = 2000;
const MAX_FAILURES = 6;

/** Follows a running validation by asking the server for new events every two seconds. */
export function useRunProgress(runId) {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("running");
  const [idea, setIdea] = useState("");
  const [error, setError] = useState(null);
  const after = useRef(0);

  useEffect(() => {
    let cancelled = false;
    let timer;
    let failures = 0;

    const tick = async () => {
      try {
        const data = await api.getRun(runId, after.current);
        if (cancelled) return;
        failures = 0;
        setIdea(data.idea);
        if (data.events.length > 0) {
          after.current = data.events[data.events.length - 1].id;
          setEvents((previous) => [...previous, ...data.events]);
        }
        setStatus(data.status);
        if (data.status !== "running") return;
      } catch (e) {
        if (cancelled) return;
        failures += 1;
        const permanent = e instanceof ApiError && (e.status === 401 || e.status === 404);
        if (permanent || failures >= MAX_FAILURES) {
          setError(e);
          return;
        }
      }
      timer = window.setTimeout(tick, POLL_MS);
    };

    tick();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [runId]);

  return { events, status, idea, error };
}