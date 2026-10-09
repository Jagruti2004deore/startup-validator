export const EVIDENCE_MAX = 8;

export function verdictTone(verdict) {
  if (verdict === "Promising") return "good";
  if (verdict === "Proceed with caution") return "caution";
  if (verdict === "Risky") return "risk";
  return "neutral";
}

/** The backend sends "Unclear: not enough verified evidence". The headline is just "Unclear". */
export function verdictLabel(verdict) {
  if (!verdict) return "Pending";
  if (verdict.startsWith("Unclear")) return "Unclear";
  return verdict;
}

// Full class names, so Tailwind can see them.
export const TONE_STYLES = {
  good: { text: "text-good", bg: "bg-good-soft", border: "border-good/20", solid: "bg-good" },
  caution: { text: "text-caution", bg: "bg-caution-soft", border: "border-caution/20", solid: "bg-caution" },
  risk: { text: "text-risk", bg: "bg-risk-soft", border: "border-risk/20", solid: "bg-risk" },
  neutral: { text: "text-muted", bg: "bg-neutral-soft", border: "border-line", solid: "bg-stone-400" },
};