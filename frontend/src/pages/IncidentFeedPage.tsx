import { useEffect, useState } from "react";
import type { Incident } from "../types/api";

const API_BASE = "http://localhost:8000/api/v1";

const ALERT_TYPES = [
  "cpu_high",
  "memory_high",
  "connections_saturated",
  "slow_query_spike",
  "replication_lag",
  "db_unreachable",
  "storage_full",
  "iops_saturated",
  "deadlock_detected"
];

export default function IncidentFeedPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [showManualTrigger, setShowManualTrigger] = useState(false);

  // Manual trigger state
  const [instanceId, setInstanceId] = useState("");
  const [alertType, setAlertType] = useState("cpu_high");
  const [severity, setSeverity] = useState("P2");
  const [metricValue, setMetricValue] = useState("");

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
          alert_type: alertType,
          severity: severity,
          metric_value: metricValue ? parseFloat(metricValue) : null,
        }),
      });
      if (res.ok) {
        alert("Manual analysis triggered");
        setShowManualTrigger(false);
        setInstanceId("");
        setMetricValue("");
        fetchIncidents();
      } else {
        const data = await res.json();
        alert(`Failed: ${data.detail || "Unknown error"}`);
      }
    } catch (e) {
      console.error("Error triggering analysis", e);
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
        <div className="mb-6 p-6 border rounded-lg bg-gray-50 flex flex-col gap-4 shadow-sm">
          <h2 className="text-lg font-bold text-gray-700 border-b pb-2">Trigger Manual DB Analysis</h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Instance ID</label>
              <input
                type="text"
                value={instanceId}
                onChange={(e) => setInstanceId(e.target.value)}
                className="border px-3 py-2 rounded w-full shadow-sm"
                placeholder="db-demo-01"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Alert Type</label>
              <select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value)}
                className="border px-3 py-2 rounded w-full shadow-sm bg-white"
              >
                {ALERT_TYPES.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Severity</label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="border px-3 py-2 rounded w-full shadow-sm bg-white"
              >
                <option value="P1">P1 - Critical</option>
                <option value="P2">P2 - High</option>
                <option value="P3">P3 - Medium</option>
                <option value="P4">P4 - Low</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Metric Value (Optional)</label>
              <input
                type="number"
                value={metricValue}
                onChange={(e) => setMetricValue(e.target.value)}
                className="border px-3 py-2 rounded w-full shadow-sm"
                placeholder="e.g. 95.5"
              />
            </div>
          </div>

          <div className="flex gap-3 justify-end mt-2">
            <button
              onClick={() => setShowManualTrigger(false)}
              className="bg-gray-400 text-white px-5 py-2 rounded shadow hover:bg-gray-500 font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleManualAnalyze}
              className="bg-green-600 text-white px-5 py-2 rounded shadow hover:bg-green-700 font-medium"
            >
              Trigger Analysis
            </button>
          </div>
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
                  <td className="px-6 py-4 font-medium text-gray-800">{inc.instance_id}</td>
                  <td className="px-6 py-4 font-mono text-sm">{inc.alert_type}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 text-xs font-bold rounded-full ${
                      inc.severity === 'P1' ? 'bg-red-100 text-red-800' :
                      inc.severity === 'P2' ? 'bg-orange-100 text-orange-800' :
                      inc.severity === 'P3' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {inc.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 text-xs font-bold rounded-full border ${
                      inc.status === 'report_ready' ? 'bg-green-50 text-green-700 border-green-200' :
                      inc.status === 'failed' ? 'bg-red-50 text-red-700 border-red-200' :
                      'bg-gray-50 text-gray-700 border-gray-200'
                    }`}>
                      {inc.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{new Date(inc.triggered_at).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <a
                      href={`/incident/${inc.incident_id}`}
                      className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                    >
                      View Report &rarr;
                    </a>
                  </td>
                </tr>
              ))}
              {incidents.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No incidents found. Wait for a webhook alert or trigger a manual analysis.
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