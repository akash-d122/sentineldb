import { BrowserRouter, Routes, Route } from "react-router-dom";
import IncidentFeedPage from "./pages/IncidentFeedPage";
import IncidentDetailPage from "./pages/IncidentDetailPage";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-white shadow-sm mb-4">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex justify-between items-center">
              <div className="font-bold text-xl text-blue-600 tracking-tight">SentinelDB</div>
              <div className="text-gray-500 text-sm">V1C Demo Dashboard</div>
            </div>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<IncidentFeedPage />} />
          <Route path="/incident/:id" element={<IncidentDetailPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
