import { Link } from "react-router-dom";
import { splitCitations } from "../lib/reportParse";

const chip =
  "rounded bg-stone-100 px-1.5 py-0.5 text-[11px] font-medium text-muted transition-colors hover:bg-accent-soft hover:text-accent";

export function CitationChips({ numbers, base }) {
  if (!numbers.length) return null;
  return (
    <span className="ml-1.5 inline-flex flex-wrap gap-1 align-baseline">
      {numbers.map((n) => (
        <Link key={n} to={`${base}#source-${n}`} className={chip}>
          {n}
        </Link>
      ))}
    </span>
  );
}

/** Text that contains [1][2] markers, shown with clickable citation chips. */
export function CitedText({ text, base }) {
  return (
    <>
      {splitCitations(text).map((part, i) =>
        part.type === "text" ? (
          <span key={i}>{part.value}</span>
        ) : (
          <Link key={i} to={`${base}#source-${part.value}`} className={`mx-0.5 ${chip}`}>
            {part.value}
          </Link>
        ),
      )}
    </>
  );
}