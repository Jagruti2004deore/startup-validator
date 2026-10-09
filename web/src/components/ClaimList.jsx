import { citeNumbers } from "../lib/reportParse";
import { CitationChips } from "./CitationChips";

export function ClaimList({ claims, citeMap, base, empty = "No verified evidence found." }) {
  if (!claims.length) return <p className="text-sm text-muted">{empty}</p>;
  return (
    <ul className="space-y-3">
      {claims.map((claim) => (
        <li key={claim.id ?? claim.text} className="flex gap-3 text-[15px] leading-relaxed">
          <span className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-stone-300" />
          <span>
            {claim.text}
            <CitationChips numbers={citeNumbers(claim, citeMap)} base={base} />
          </span>
        </li>
      ))}
    </ul>
  );
}