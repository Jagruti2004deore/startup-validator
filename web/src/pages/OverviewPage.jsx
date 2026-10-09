import { AlertTriangle, ArrowRight, CheckCircle2 } from "lucide-react";
import { Link, useOutletContext } from "react-router-dom";
import { EvidenceMeter } from "../components/EvidenceMeter";
import { LinkButton } from "../components/LinkButton";
import { Card } from "../components/ui";
import {
  checklistRows, insightCards, nextStep, signalCards, verdictSentence,
} from "../lib/insights";
import { EVIDENCE_MAX, TONE_STYLES, verdictLabel, verdictTone } from "../lib/verdict";

function VerdictCard({ report, score }) {
  const tone = TONE_STYLES[verdictTone(report.verdict)];
  const value = score?.evidence_score ?? report.evidence_score ?? 0;
  const max = score?.max_score ?? EVIDENCE_MAX;
  const sentence = verdictSentence(score);

  return (
    <Card className={`animate-fade-up border p-6 md:p-8 ${tone.bg} ${tone.border}`}>
      <p className={`text-xs font-semibold uppercase tracking-widest ${tone.text}`}>Verdict</p>
      <p className={`mt-1 text-4xl font-semibold uppercase tracking-tight ${tone.text}`}>
        {verdictLabel(report.verdict)}
      </p>
      {sentence && <p className="mt-3 max-w-xl text-[15px] leading-relaxed">{sentence}</p>}
      <div className="mt-6">
        <p className="text-xs text-muted">Evidence strength</p>
        <div className="mt-2 flex items-center gap-3">
          <EvidenceMeter value={value} max={max} barClass={tone.solid} />
          <span className="text-sm font-medium tabular-nums">
            {value} / {max}
          </span>
        </div>
      </div>
    </Card>
  );
}

function SignalGrid({ score }) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {signalCards(score).map((card) => (
        <Card key={card.key} className="p-4">
          <p className="text-xs text-muted">{card.label}</p>
          <p className="mt-2 flex items-center gap-2 text-[15px] font-medium">
            <span className={`h-2 w-2 shrink-0 rounded-full ${TONE_STYLES[card.tone].solid}`} />
            {card.value}
          </p>
        </Card>
      ))}
    </div>
  );
}

function Checklist({ score, runId }) {
  return (
    <section>
      <h2 className="text-lg font-semibold tracking-tight">Why this verdict?</h2>
      <Card className="mt-4 divide-y divide-line/70">
        {checklistRows(score).map((row) => (
          <div key={row.key} className="flex items-center gap-3 px-5 py-3.5">
            {row.passed ? (
              <CheckCircle2 className="h-5 w-5 shrink-0 text-good" />
            ) : (
              <AlertTriangle className="h-5 w-5 shrink-0 text-caution" />
            )}
            <span className={row.passed ? "" : "text-muted"}>{row.label}</span>
            {row.passed && row.category && (
              <Link
                to={`/validations/${runId}/evidence?focus=${row.category}`}
                className="ml-auto shrink-0 text-sm font-medium text-accent hover:underline"
              >
                View evidence
              </Link>
            )}
          </div>
        ))}
      </Card>
    </section>
  );
}

function Insights({ report, score }) {
  return (
    <section>
      <h2 className="text-lg font-semibold tracking-tight">Key insights</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {insightCards(report.verified, score).map((card) => (
          <Card key={card.key} className="p-5">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted">{card.label}</p>
            <p className="mt-3 text-[15px] leading-relaxed">{card.text}</p>
            {card.detail && <p className="mt-3 text-sm text-muted">{card.detail}</p>}
          </Card>
        ))}
      </div>
    </section>
  );
}

function NextStep({ score }) {
  const step = nextStep(score);
  return (
    <section>
      <h2 className="text-lg font-semibold tracking-tight">Recommended next step</h2>
      <Card className="mt-4 border-l-4 border-l-accent p-5">
        <p className="text-[15px] leading-relaxed">{step.text}</p>
        <p className="mt-3 text-xs text-muted">{step.basis}</p>
      </Card>
    </section>
  );
}

export default function OverviewPage() {
  const { report, runId } = useOutletContext();
  const score = report.score;

  return (
    <div className="space-y-10">
      <VerdictCard report={report} score={score} />

      {score ? (
        <>
          <SignalGrid score={score} />
          <Checklist score={score} runId={runId} />
          <Insights report={report} score={score} />
          <NextStep score={score} />
        </>
      ) : (
        <Card className="p-5 text-sm text-muted">
          A detailed breakdown isn&apos;t available for this older validation. The full report still
          has everything that was saved.
        </Card>
      )}

      <div className="flex flex-wrap items-center gap-4">
        <LinkButton to={`/validations/${runId}/report`}>
          View Full Validation Report <ArrowRight className="h-4 w-4" />
        </LinkButton>
        <Link
          to={`/validations/${runId}/evidence`}
          className="text-sm font-medium text-accent hover:underline"
        >
          See the evidence
        </Link>
      </div>
    </div>
  );
}