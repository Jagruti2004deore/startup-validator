import { BrowserRouter, Route, Routes } from "react-router-dom";
import { ErrorBoundary } from "./components/ErrorBoundary";
import Layout from "./components/Layout";
import EvidencePage from "./pages/EvidencePage";
import MemoryPage from "./pages/MemoryPage";
import OverviewPage from "./pages/OverviewPage";
import PastValidationsPage from "./pages/PastValidationsPage";
import ReportPage from "./pages/ReportPage";
import ResultLayout from "./pages/ResultLayout";
import SettingsPage from "./pages/SettingsPage";
import SourcesPage from "./pages/SourcesPage";
import ValidatePage from "./pages/ValidatePage";
import VerificationPage from "./pages/VerificationPage";

function NotFound() {
  return (
    <div className="animate-fade-up">
      <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
      <p className="mt-2 text-muted">That page doesn&apos;t exist. Use the menu to find your way back.</p>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<ValidatePage />} />
            <Route path="validations" element={<PastValidationsPage />} />
            <Route path="validations/:runId" element={<ResultLayout />}>
              <Route index element={<OverviewPage />} />
              <Route path="report" element={<ReportPage />} />
              <Route path="evidence" element={<EvidencePage />} />
              <Route path="sources" element={<SourcesPage />} />
              <Route path="verification" element={<VerificationPage />} />
            </Route>
            <Route path="memory" element={<MemoryPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}