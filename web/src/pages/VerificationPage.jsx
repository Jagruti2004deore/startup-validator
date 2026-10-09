import { useOutletContext } from "react-router-dom";
import { Expandable } from "../components/Expandable";
import { Card } from "../components/ui";
import { CATEGORY_LABEL } from "../lib/category";
import { plural } from "../lib/format";
import { stageLabel } from "../lib/log";
import { groupReasons, reasonLabel } from "../lib/reasons";

export default function VerificationPage() {
  const { report, events } = useOutletContext();
  const verified = report.verified.length;
  const dropped = report.dropped.length;
  const reasons = groupReasons(report.dropped);

  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Verification details</h2>
        <p className="mt-1 text-sm text-muted">
          Every statement the research produced was checked against the text of its source. Claims that
          failed are listed here. Showing them is how this report earns your trust.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Card className="p-5">
          <p className="text-2xl font-semibold tabular-nums">{verified}</p>
          <p className="mt-1 text-sm text-muted">{plural(verified, "claim")} verified</p>
        </Card>
        <Card className="p-5">
          <p className="text-2xl font-semibold tabular-nums">{dropped}</p>
          <p className="mt-1 text-sm text-muted">{plural(dropped, "claim")} rejected</p>
        </Card>
      </div>

      <section>
        <h3 className="font-medium">Claims rejected during verification</h3>
        {dropped === 0 ? (
          <p className="mt-2 text-sm text-muted">No claims were rejected.</p>
        ) : (
          <>
            <ul className="mt-3 space-y-2">
              {reasons.map((group) => (
                <li
                  key={group.label}
                  className="flex items-center justify-between gap-4 rounded-xl border border-line bg-white px-4 py-3 text-sm"
                >
                  <span>{group.label}</span>
                  <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-muted">
                    {group.count}
                  </span>
                </li>
              ))}
            </ul>

            <Card className="mt-4 px-5">
              <Expandable className="py-4" summary={<span className="font-medium">See the rejected claims</span>}>
                <ul className="-ml-7 divide-y divide-line/70">
                  {report.dropped.map((claim) => (
                    <li key={claim.id} className="py-3 text-sm leading-relaxed">
                      <p>{claim.text}</p>
                      <p className="mt-1 text-xs text-muted">
                        {CATEGORY_LABEL[claim.category] ?? "Claim"}: {reasonLabel(claim.drop_reason)}
                      </p>
                    </li>
                  ))}
                </ul>
              </Expandable>
            </Card>
          </>
        )}
      </section>

      <section>
        <Card className="px-5">
          <Expandable className="py-4" summary={<span className="font-medium">Research log</span>}>
            {events.length === 0 ? (
              <p className="text-sm text-muted">No log was saved.</p>
            ) : (
              <ul className="-ml-7 space-y-2 text-sm">
                {events.map((event) => (
                  <li key={event.id} className="flex gap-3">
                    <span className="w-16 shrink-0 tabular-nums text-xs text-muted">
                      {(event.time || "").slice(11, 19)}
                    </span>
                    <span className="w-40 shrink-0 text-muted">{stageLabel(event.node)}</span>
                    <span className="min-w-0">{event.message}</span>
                  </li>
                ))}
              </ul>
            )}
          </Expandable>
        </Card>
      </section>
    </div>
  );
}