import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/** Scrolls to the element named in the address (#source-3) once the page has rendered. */
export function useHashScroll() {
  const { hash } = useLocation();
  useEffect(() => {
    if (!hash) return;
    document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [hash]);
}