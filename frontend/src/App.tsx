import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import IncidentFeedPage from "./pages/IncidentFeedPage";
import IncidentDetailPage from "./pages/IncidentDetailPage";
import ConfigPage from "./pages/ConfigPage";

function AppContent() {
  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm mb-4">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-6">
              <Link to="/" className="font-bold text-xl text-blue-600 tracking-tight">SentinelDB</Link>
              <Link to="/config" className="text-gray-600 hover:text-gray-900 text-sm font-medium">Settings</Link>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-gray-500 text-sm">V2 Internal Dashboard</div>
            </div>
          </div>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<IncidentFeedPage />} />
        <Route path="/incident/:id" element={<IncidentDetailPage />} />
        <Route path="/config" element={<ConfigPage />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
