import { Download } from "lucide-react";
import { Link, useOutletContext } from "react-router-dom";
import { CitationChips, CitedText } from "../components/CitationChips";
import { ClaimList } from "../components/ClaimList";
import { SourcesList } from "../components/SourcesList";
import { Button } from "../components/ui";
import { VerdictBadge } from "../components/VerdictBadge";
import { claimsByCategory } from "../lib/category";
import { downloadText, formatDate } from "../lib/format";
import { CHECK_LABELS, insightCards, verdictSentence } from "../lib/insights";
import { citeNumbersAll } from "../lib/reportParse";
import { useHashScroll } from "../hooks/useHashScroll";
import { EVIDENCE_MAX } from "../lib/verdict";

const SECTIONS = [
  ["s01", "01", "Executive Summary"],
  ["s02", "02", "Market Overview"],
  ["s03", "03", "Competitor Landscape"],
  ["s04", "04", "Pricing"],
  ["s05", "05", "Customer Demand"],
  ["s06", "06", "Market Size"],
  ["s07", "07", "Recent Activity"],
  ["s08", "08", "Risks"],
  ["s09", "09", "Differentiation Opportunities"],
  ["s10", "10", "Founder Memory"],
  ["s11", "11", "Evidence Gaps"],
  ["s12", "12", "Sources"],
];

function Section({ id, number, title, children }) {
  return (
    <section id={id} className="scroll-mt-28 border-t border-line pt-8">
      <p className="text-xs font-medium tracking-widest text-muted">{number}</p>
      <h2 className="mt-1 text-xl font-semibold tracking-tight">{title}</h2>
      <div className="mt-4 space-y-3">{children}</div>
    </section>
  );
}

function CompetitorTable({ competitors, citeMap, base }) {
  if (!competitors.length) {
    return <p className="text-sm text-muted">No verified evidence found.</p>;
  }
  const rows = competitors.map((c) => ({
    name: c.name,
    offer: c.claims[0]?.text ?? "",
    evidence: c.claims.find((claim) => claim.evidence_quote)?.evidence_quote ?? "",
    pricing: c.pricing[0]?.text ?? "",
    cites: citeNumbersAll([...c.claims, ...c.pricing], citeMap),
  }));

  return (
    <>
      <div className="hidden overflow-hidden rounded-2xl border border-line bg-white md:block">
        <table className="w-full text-left text-sm">
          <thead className="bg-stone-50 text-xs uppercase tracking-wide text-muted">
            <tr>
              <th className="px-4 py-3 font-medium">Competitor</th>
              <th className="px-4 py-3 font-medium">What they offer</th>
              <th className="px-4 py-3 font-medium">Relevant evidence</th>
              <th className="px-4 py-3 font-medium">Pricing</th>
              <th className="px-4 py-3 font-medium">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line align-top">
            {rows.map((row) => (
              <tr key={row.name}>
                <td className="px-4 py-3 font-medium">{row.name}</td>
                <td className="px-4 py-3">{row.offer}</td>
                <td className="px-4 py-3 text-muted">{row.evidence ? `“${row.evidence}”` : "-"}</td>
                <td className="px-4 py-3">{row.pricing || <span className="text-muted">Pricing not verified</span>}</td>
                <td className="px-4 py-3">
                  <CitationChips numbers={row.cites} base={base} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="space-y-3 md:hidden">
        {rows.map((row) => (
          <div key={row.name} className="rounded-2xl border border-line bg-white p-4">
            <p className="font-medium">{row.name}</p>
            <p className="mt-2 text-sm">{row.offer}</p>
            {row.evidence && <p className="mt-2 text-sm text-muted">“{row.evidence}”</p>}
            <p className="mt-2 text-sm">
              {row.pricing || <span className="text-muted">Pricing not verified</span>}
            </p>
            <p className="mt-2">
              <CitationChips numbers={row.cites} base={base} />
            </p>
          </div>
        ))}
      </div>
    </>
  );
}

export default function ReportPage() {
  const { report, runId, parsed, sourceList, citeMap } = useOutletContext();
  useHashScroll();

  const base = `/validations/${runId}/report`;
  const score = report.score;
  const byCategory = claimsByCategory(report.verified);
  const pricing = report.competitors.flatMap((c) => c.pricing);
  const gaps = score ? score.items.filter((i) => !i.passed) : [];
  const summary = parsed.summary || verdictSentence(score);
  const market = score ? insightCards(report.verified, score)[0].text : "";

  return (
    <div className="lg:grid lg:grid-cols-[180px_minmax(0,1fr)] lg:gap-12">
      <aside className="hidden lg:block">
        <nav className="sticky top-24 space-y-1 text-sm" aria-label="On this page">
          <p className="mb-2 text-xs font-medium uppercase tracking-widest text-muted">On this page</p>
          {SECTIONS.map(([id, number, title]) => (
            <Link
              key={id}
              to={`${base}#${id}`}
              className="flex gap-2 rounded px-2 py-1 text-muted hover:bg-stone-100 hover:text-ink"
            >
              <span className="tabular-nums">{number}</span>
              <span>{title}</span>
            </Link>
          ))}
        </nav>
      </aside>

      <article className="min-w-0 space-y-10">
        <header>
          <p className="text-xs font-medium uppercase tracking-widest text-muted">Validation Report</p>
          <dl className="mt-4 grid gap-5 sm:grid-cols-[1fr_auto_auto]">
            <div>
              <dt className="text-xs text-muted">Idea</dt>
              <dd className="mt-1 text-[15px] leading-relaxed">{report.idea}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted">Verdict</dt>
              <dd className="mt-1"><VerdictBadge verdict={report.verdict} /></dd>
            </div>
            <div>
              <dt className="text-xs text-muted">Evidence</dt>
              <dd className="mt-1 text-sm font-medium tabular-nums">
                {score?.evidence_score ?? report.evidence_score ?? "-"} / {score?.max_score ?? EVIDENCE_MAX}
              </dd>
            </div>
          </dl>
          <div className="mt-5 flex flex-wrap items-center gap-4">
            <Button
              variant="secondary"
              onClick={() => downloadText("startup-validation.md", report.report_md)}
              disabled={!report.report_md}
            >
              <Download className="h-4 w-4" /> Download
            </Button>
            <span className="text-xs text-muted">{formatDate(report.created_at, true)}</span>
          </div>
        </header>

        <Section id="s01" number="01" title="Executive Summary">
          <p className="text-[15px] leading-relaxed">
            <CitedText text={summary || "No summary was saved."} base={base} />
          </p>
        </Section>

        <Section id="s02" number="02" title="Market Overview">
          <p className="text-[15px] leading-relaxed">{market || "Not available for this older validation."}</p>
        </Section>

        <Section id="s03" number="03" title="Competitor Landscape">
          <p className="text-sm text-muted">Only competitors that passed verification are listed.</p>
          <CompetitorTable competitors={report.competitors} citeMap={citeMap} base={base} />
        </Section>

        <Section id="s04" number="04" title="Pricing">
          <ClaimList
            claims={pricing}
            citeMap={citeMap}
            base={base}
            empty="Pricing not verified for the competitors found."
          />
        </Section>

        <Section id="s05" number="05" title="Customer Demand">
          <ClaimList claims={byCategory.demand_signal ?? []} citeMap={citeMap} base={base} />
        </Section>

        <Section id="s06" number="06" title="Market Size">
          <ClaimList claims={byCategory.market_size ?? []} citeMap={citeMap} base={base} />
          {(byCategory.market_size ?? []).length >= 2 && (
            <p className="text-sm text-muted">
              These figures come from different publishers and do not agree. Treat them as a range, not
              a single number.
            </p>
          )}
        </Section>

        <Section id="s07" number="07" title="Recent Activity">
          <ClaimList claims={byCategory.recent_activity ?? []} citeMap={citeMap} base={base} />
        </Section>

        <Section id="s08" number="08" title="Risks">
          <ClaimList claims={byCategory.failure_or_risk ?? []} citeMap={citeMap} base={base} />
        </Section>

        <Section id="s09" number="09" title="Differentiation Opportunities">
          <ClaimList
            claims={byCategory.differentiation_gap ?? []}
            citeMap={citeMap}
            base={base}
            empty="No differentiation opportunity could be verified."
          />
          {(byCategory.differentiation_gap ?? []).length > 0 && (
            <p className="text-sm text-muted">
              Analysis based on the verified competitor facts above, not a statement from a source.
            </p>
          )}
        </Section>

        <Section id="s10" number="10" title="Founder Memory">
          {(byCategory.conflict_with_past_notes ?? []).length > 0 ? (
            <ul className="space-y-3">
              {byCategory.conflict_with_past_notes.map((claim) => (
                <li key={claim.id} className="text-[15px] leading-relaxed">
                  {claim.text}
                  {claim.evidence_quote && (
                    <span className="mt-1 block text-sm text-muted">
                      From your memories: “{claim.evidence_quote}”
                    </span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted">
              {score?.items.find((i) => i.key === "memory")?.passed
                ? "Your saved memories were checked. None conflicts with this idea."
                : "Your saved memories couldn't be checked for this validation."}
            </p>
          )}
        </Section>

        <Section id="s11" number="11" title="Evidence Gaps">
          {!score ? (
            <p className="text-sm text-muted">Not available for this older validation.</p>
          ) : gaps.length === 0 ? (
            <p className="text-sm text-muted">Every checklist item was verified.</p>
          ) : (
            <ul className="space-y-2 text-[15px]">
              {gaps.map((item) => (
                <li key={item.key} className="flex gap-3">
                  <span className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-caution" />
                  <span>
                    {CHECK_LABELS[item.key]?.[1] ?? item.label}{" "}
                    <span className="text-sm text-muted">
                      ({item.found} of {item.needed} verified)
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section id="s12" number="12" title="Sources">
          <SourcesList sources={sourceList} />
        </Section>
      </article>
    </div>
  );
}