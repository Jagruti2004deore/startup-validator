import { TONE_STYLES, verdictLabel, verdictTone } from "../lib/verdict";

export function VerdictBadge({ verdict }) {
  const tone = TONE_STYLES[verdictTone(verdict)];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${tone.bg} ${tone.text}`}
    >
      {verdictLabel(verdict)}
    </span>
  );
}