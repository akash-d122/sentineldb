import { BrowserRouter, Routes, Route } from "react-router-dom";
import IncidentFeedPage from "./pages/IncidentFeedPage";
import IncidentDetailPage from "./pages/IncidentDetailPage";

import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import IncidentFeedPage from "./pages/IncidentFeedPage";
import IncidentDetailPage from "./pages/IncidentDetailPage";
import ConfigPage from "./pages/ConfigPage";
import { AuthProvider, useAuth } from "./auth/AuthProvider";

function AppContent() {
  const { signOut } = useAuth();

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
              <button
                onClick={signOut}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Sign Out
              </button>
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
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
