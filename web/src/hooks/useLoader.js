import { useEffect, useState } from "react";

/**
 * Loads data once, and again whenever `version` changes.
 * `load` must be a stable function (defined outside the component),
 * otherwise it would reload on every render.
 *
 * While reloading, the previous data stays visible (`refreshing` is true),
 * so lists do not flash empty after an add or a delete.
 */
export function useLoader(load, version = 0) {
  const [result, setResult] = useState(null);

  useEffect(() => {
    let cancelled = false;
    load()
      .then((data) => {
        if (!cancelled) setResult({ version, phase: "ready", data });
      })
      .catch((error) => {
        if (!cancelled) setResult({ version, phase: "error", error });
      });
    return () => {
      cancelled = true;
    };
  }, [load, version]);

  if (!result) return { phase: "loading" };
  if (result.version !== version) {
    return result.phase === "ready" ? { ...result, refreshing: true } : { phase: "loading" };
  }
  return result;
}