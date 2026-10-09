import { useEffect } from "react";
import { ArrowUpRight, ShieldCheck } from "lucide-react";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { Expandable } from "../components/Expandable";
import { Card } from "../components/ui";
import { CATEGORY_LABEL, CATEGORY_ORDER, claimsByCategory } from "../lib/category";
import { domainOf, safeUrl } from "../lib/format";

function Detail({ label, children }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-muted">{label}</dt>
      <dd className="mt-1">{children}</dd>
    </div>
  );
}

function EvidenceItem({ claim, sourceRows }) {
  const sources = (claim.source_nos || []).map((no) => sourceRows[no]).filter(Boolean);
  const derived = claim.category === "differentiation_gap";
  const fromNotes = claim.category === "conflict_with_past_notes";
  const websites = [...new Set(sources.map((s) => domainOf(s.url)).filter(Boolean))];

  return (
    <Expandable
      className="py-4"
      summary={
        <span className="block">
          <span className="line-clamp-2 text-[15px] leading-relaxed">{claim.text}</span>
          {websites.length > 0 && (
            <span className="mt-1 block text-xs text-muted">{websites.join(", ")}</span>
          )}
        </span>
      }
    >
      <dl className="space-y-4 text-sm leading-relaxed">
        <Detail label="Claim">{claim.text}</Detail>
        <Detail label="Supporting evidence">
          {derived ? (
            <span className="text-muted">
              Analysis based on the verified competitor claims, not a statement from a source.
            </span>
          ) : claim.evidence_quote ? (
            <blockquote className="border-l-2 border-line pl-3 text-muted">
              “{claim.evidence_quote}”
            </blockquote>
          ) : (
            <span className="text-muted">No passage was saved for this claim.</span>
          )}
        </Detail>
        {fromNotes && <Detail label="Source">Your saved memories</Detail>}
        {!fromNotes && sources.length > 0 && (
          <Detail label={derived ? "Built from" : "Source"}>
            <ul className="space-y-3">
              {sources.map((s) => (
                <li key={s.source_no}>
                  <p className="font-medium">{s.title || domainOf(s.url)}</p>
                  <p className="text-xs text-muted">{domainOf(s.url)}</p>
                  {safeUrl(s.url) && (
                    <>
                      <p className="mt-1 break-all text-xs text-muted">{s.url}</p>
                      <a
                        href={safeUrl(s.url)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1 inline-flex items-center gap-1 font-medium text-accent hover:underline"
                      >
                        View source <ArrowUpRight className="h-4 w-4" />
                      </a>
                    </>
                  )}
                </li>
              ))}
            </ul>
          </Detail>
        )}
      </dl>
    </Expandable>
  );
}

export default function EvidencePage() {
  const { report } = useOutletContext();
  const [params] = useSearchParams();
  const focus = params.get("focus");

  const groups = claimsByCategory(report.verified);
  const categories = CATEGORY_ORDER.filter((category) => groups[category]?.length);
  const sourceRows = Object.fromEntries(report.sources.map((s) => [s.source_no, s]));

  useEffect(() => {
    if (focus) {
      document.getElementById(`group-${focus}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [focus]);

  if (!categories.length) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title="No verified evidence"
        text="None of the research findings passed verification, so there is nothing to show here."
      />
    );
  }

  return (
    <div className="max-w-3xl">
      <h2 className="text-lg font-semibold tracking-tight">Verified Evidence</h2>
      <p className="mt-1 text-sm text-muted">
        Every item below was checked against the text of its source. Open an item to see exactly what
        supports it.
      </p>

      <div className="mt-6 space-y-4">
        {categories.map((category, index) => (
          <Card key={category} className="scroll-mt-28 px-5" id={`group-${category}`}>
            <Expandable
              className="py-4"
              defaultOpen={focus ? focus === category : index === 0}
              summary={
                <span className="flex items-center justify-between gap-3">
                  <span className="font-medium">{CATEGORY_LABEL[category]}</span>
                  <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-muted">
                    {groups[category].length}
                  </span>
                </span>
              }
            >
              <div className="-ml-7 divide-y divide-line/70">
                {groups[category].map((claim) => (
                  <EvidenceItem key={claim.id} claim={claim} sourceRows={sourceRows} />
                ))}
              </div>
            </Expandable>
          </Card>
        ))}
      </div>
    </div>
  );
}