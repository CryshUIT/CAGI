import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import OverviewPage from "./pages/OverviewPage";
import IncidentsPage from "./pages/IncidentsPage";
import InvestigationPage from "./pages/InvestigationPage";
import ExplainabilityPage from "./pages/ExplainabilityPage";
import NewAnalysisPage from "./pages/NewAnalysisPage";
import SettingsPage from "./pages/SettingsPage";
import { ThetaProvider } from "./ThetaContext";

export default function App() {
  return (
    <ThetaProvider>
      <div className="flex h-screen w-screen overflow-hidden bg-bg text-text">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/incidents" element={<IncidentsPage />} />
            <Route path="/new-analysis" element={<NewAnalysisPage />} />
            <Route path="/investigation" element={<InvestigationPage />} />
            <Route path="/investigation/:incidentId" element={<InvestigationPage />} />
            <Route path="/explainability" element={<ExplainabilityPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </ThetaProvider>
  );
}
