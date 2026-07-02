import { useEffect, useState } from "react";
import type { Incident } from "../types/api";

const API_BASE = "http://localhost:8000/api/v1";

export default function IncidentFeedPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [showManualTrigger, setShowManualTrigger] = useState(false);
  const [instanceId, setInstanceId] = useState("");

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${API_BASE}/incidents`);
      if (res.ok) {
        const data = await res.json();
        setIncidents(data);
      }
    } catch (e) {
      console.error("Failed to fetch incidents", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleManualAnalyze = async () => {
    if (!instanceId) return alert("Please enter instance ID");
    try {
      const res = await fetch(`${API_BASE}/incidents/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          instance_id: instanceId,
          alert_type: "db_unreachable",
          severity: "P3",
        }),
      });
      if (res.ok) {
        alert("Manual analysis triggered");
        setShowManualTrigger(false);
        setInstanceId("");
        fetchIncidents();
      } else {
        const data = await res.json();
        alert(`Failed: ${data.detail || "Unknown error"}`);
      }
    } catch (e) {
      alert("Error triggering analysis");
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Incident Feed</h1>
        <button
          onClick={() => setShowManualTrigger(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700"
        >
          Run Manual Analysis
        </button>
      </div>

      {showManualTrigger && (
        <div className="mb-6 p-4 border rounded bg-gray-50 flex gap-4 items-center">
          <label className="font-semibold text-gray-700">Instance ID:</label>
          <input
            type="text"
            value={instanceId}
            onChange={(e) => setInstanceId(e.target.value)}
            className="border px-3 py-1 rounded w-64"
            placeholder="e.g. pg-demo-01"
          />
          <button
            onClick={handleManualAnalyze}
            className="bg-green-600 text-white px-4 py-1 rounded shadow hover:bg-green-700"
          >
            Trigger
          </button>
          <button
            onClick={() => setShowManualTrigger(false)}
            className="bg-gray-400 text-white px-4 py-1 rounded shadow hover:bg-gray-500"
          >
            Cancel
          </button>
        </div>
      )}

      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="overflow-x-auto bg-white shadow rounded-lg">
          <table className="min-w-full text-left">
            <thead className="bg-gray-100 border-b">
              <tr>
                <th className="px-6 py-3 font-semibold text-gray-700">Instance</th>
                <th className="px-6 py-3 font-semibold text-gray-700">Alert</th>
                <th className="px-6 py-3 font-semibold text-gray-700">Severity</th>
                <th className="px-6 py-3 font-semibold text-gray-700">Status</th>
                <th className="px-6 py-3 font-semibold text-gray-700">Time</th>
                <th className="px-6 py-3 font-semibold text-gray-700">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y text-gray-600">
              {incidents.map((inc) => (
                <tr key={inc.incident_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">{inc.instance_id}</td>
                  <td className="px-6 py-4">{inc.alert_type}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-bold rounded-full ${
                      inc.severity === 'P1' ? 'bg-red-100 text-red-800' :
                      inc.severity === 'P2' ? 'bg-orange-100 text-orange-800' :
                      inc.severity === 'P3' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {inc.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-bold rounded-full ${
                      inc.status === 'report_ready' ? 'bg-green-100 text-green-800' :
                      inc.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {inc.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">{new Date(inc.triggered_at).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <a
                      href={`/incident/${inc.incident_id}`}
                      className="text-blue-600 hover:underline"
                    >
                      View Report
                    </a>
                  </td>
                </tr>
              ))}
              {incidents.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No incidents found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
