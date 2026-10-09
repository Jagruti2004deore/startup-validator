import { useMemo } from "react";
import { Link, NavLink, Outlet, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { ErrorPanel } from "../components/ErrorPanel";
import { LoadingBlock } from "../components/LoadingBlock";
import { VerdictBadge } from "../components/VerdictBadge";
import { Button, Notice } from "../components/ui";
import { useReport } from "../hooks/useReport";
import { failedRunMessage, friendlyError } from "../lib/errors";
import { truncate } from "../lib/format";
import { buildCitationMap, buildSourceList, parseReport } from "../lib/reportParse";

const TABS = [
  { path: "", label: "Overview" },
  { path: "/report", label: "Full report" },
  { path: "/evidence", label: "Evidence" },
  { path: "/sources", label: "Sources" },
  { path: "/verification", label: "Verification" },
];

const tabClass = ({ isActive }) =>
  `whitespace-nowrap border-b-2 px-1 pb-3 pt-2 text-sm font-medium transition-colors ${
    isActive ? "border-accent text-accent" : "border-transparent text-muted hover:text-ink"
  }`;

function ReadyResult({ runId, report, events }) {
  const shared = useMemo(() => {
    const parsed = parseReport(report.report_md);
    return {
      parsed,
      sourceList: buildSourceList(parsed.sources, report.sources),
      citeMap: buildCitationMap(parsed.sources, report.sources),
    };
  }, [report]);

  return (
    <div>
      <Link
        to="/validations"
        className="inline-flex items-center gap-1 text-sm text-muted hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" /> Past Validations
      </Link>

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">
          {truncate(report.title || report.idea, 90)}
        </h1>
        <VerdictBadge verdict={report.verdict} />
      </div>

      <nav
        aria-label="Validation sections"
        className="sticky top-0 z-10 -mx-5 mt-5 flex gap-6 overflow-x-auto border-b border-line bg-canvas/95 px-5 backdrop-blur md:-mx-8 md:px-8"
      >
        {TABS.map((tab) => (
          <NavLink
            key={tab.label}
            to={`/validations/${runId}${tab.path}`}
            end={tab.path === ""}
            className={tabClass}
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      <div className="pt-8">
        <Outlet context={{ runId, report, events, ...shared }} />
      </div>
    </div>
  );
}

export default function ResultLayout() {
  const { runId } = useParams();
  const navigate = useNavigate();
  const data = useReport(runId);

  if (data.phase === "loading") return <LoadingBlock />;

  if (data.phase === "running") {
    return (
      <Notice
        title="This validation is still in progress"
        action={
          <Button
            onClick={() => {
              localStorage.setItem("sv_active_run", runId);
              navigate("/");
            }}
          >
            View progress
          </Button>
        }
      >
        The research hasn&apos;t finished yet. You can watch it from the Validate Idea page.
      </Notice>
    );
  }

  if (data.phase === "error") {
    return <ErrorPanel error={friendlyError(data.error)} onRetry={data.retry} />;
  }

  if (data.report.status === "failed") {
    const friendly = failedRunMessage(data.events);
    return (
      <Notice
        title={friendly.title}
        action={<Button variant="secondary" onClick={() => navigate("/")}>Validate another idea</Button>}
      >
        {friendly.message}
      </Notice>
    );
  }

  return <ReadyResult runId={runId} report={data.report} events={data.events} />;
}