import { useOutletContext } from "react-router-dom";
import { SourcesList } from "../components/SourcesList";
import { useHashScroll } from "../hooks/useHashScroll";
import { plural } from "../lib/format";

export default function SourcesPage() {
  const { report, sourceList } = useOutletContext();
  useHashScroll();
  const unused = Math.max(report.sources.length - sourceList.length, 0);

  return (
    <div className="max-w-3xl">
      <h2 className="text-lg font-semibold tracking-tight">Sources</h2>
      <p className="mt-1 text-sm text-muted">
        These are the pages the verified findings rely on. The numbers match the report.
      </p>
      <div className="mt-6">
        <SourcesList sources={sourceList} />
      </div>
      {unused > 0 && (
        <p className="mt-6 text-xs text-muted">
          {unused} more {plural(unused, "page")} reviewed during research but not used in the report.
        </p>
      )}
    </div>
  );
}