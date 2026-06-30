import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import type { Incident, IncidentReport } from "../types/api";

const API_BASE = "http://localhost:8000/api/v1";

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [report, setReport] = useState<IncidentReport | null>(null);
  const [statusMsg, setStatusMsg] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const incRes = await fetch(`${API_BASE}/incidents/${id}`);
        if (incRes.ok) {
          setIncident(await incRes.json());
        }

        const repRes = await fetch(`${API_BASE}/incidents/${id}/report`);
        if (repRes.status === 200) {
          setReport(await repRes.json());
          setStatusMsg("");
        } else if (repRes.status === 202) {
          const msg = await repRes.json();
          setStatusMsg(msg.message);
        } else {
          setStatusMsg("Failed to fetch report or report not found.");
        }
      } catch (e) {
        setStatusMsg("Error fetching details.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [id]);

  if (loading) return <div className="p-8 text-gray-500">Loading incident...</div>;
  if (!incident) return <div className="p-8 text-red-500">Incident not found.</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6">
        <Link to="/" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Feed</Link>
        <div className="flex items-center gap-4 mb-2">
          <h1 className="text-3xl font-bold text-gray-800">
            [{incident.severity}] {incident.alert_type}
          </h1>
          <span className="px-3 py-1 bg-gray-200 rounded-full text-sm font-semibold">
            {incident.instance_id}
          </span>
        </div>
        <p className="text-gray-500 text-sm">
          Triggered: {new Date(incident.triggered_at).toLocaleString()} | Status: {incident.status}
        </p>
      </div>

      {!report ? (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <p className="text-yellow-700">{statusMsg || "Report is not ready yet."}</p>
        </div>
      ) : (
        <div className="space-y-6">
          <section className="bg-white p-6 shadow rounded-lg border-t-4 border-blue-600">
            <h2 className="text-xl font-bold text-gray-800 mb-2 flex items-center gap-2">
              ROOT CAUSE
              <span className={`px-2 py-1 text-xs rounded-full text-white ${
                report.rca_strength === 'High' ? 'bg-green-600' :
                report.rca_strength === 'Medium' ? 'bg-yellow-500' : 'bg-red-500'
              }`}>
                Strength: {report.rca_strength}
              </span>
            </h2>
            <p className="text-gray-700 font-medium text-lg leading-relaxed">
              {report.root_cause_summary}
            </p>
          </section>

          <section className="bg-white p-6 shadow rounded-lg">
            <h2 className="text-lg font-bold text-gray-800 mb-3">WHY THIS IS MOST LIKELY</h2>
            <ul className="list-disc pl-5 text-gray-700 space-y-1">
              {report.why_most_likely.map((reason, i) => (
                <li key={i}>{reason}</li>
              ))}
            </ul>
          </section>

          <section className="bg-white p-6 shadow rounded-lg">
            <h2 className="text-lg font-bold text-gray-800 mb-3">EVIDENCE</h2>
            <div className="space-y-3">
              {report.evidence.map((ev) => (
                <div key={ev.id} className="flex gap-3 text-sm border-b pb-2">
                  <div className="w-24 shrink-0 font-semibold text-gray-500">[{ev.source}]</div>
                  <div className="flex-1 text-gray-800">{ev.display_text}</div>
                  <div className={`font-bold w-20 text-right ${
                    ev.status === 'OK' ? 'text-green-600' :
                    ev.status === 'WARN' ? 'text-yellow-600' :
                    ev.status === 'CRITICAL' ? 'text-red-600' : 'text-gray-400'
                  }`}>
                    {ev.status}
                  </div>
                </div>
              ))}
            </div>
            
            {report.missing_evidence.length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <h3 className="font-bold text-gray-700 mb-2">MISSING EVIDENCE</h3>
                <ul className="list-disc pl-5 text-gray-600 text-sm">
                  {report.missing_evidence.map((me, i) => <li key={i}>{me}</li>)}
                </ul>
              </div>
            )}
          </section>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <section className="bg-green-50 p-6 shadow rounded-lg border border-green-200">
              <h2 className="text-lg font-bold text-green-800 mb-3">SAFE NEXT ACTIONS</h2>
              <ul className="list-decimal pl-5 text-green-900 space-y-2 text-sm">
                {report.safe_next_actions.map((act, i) => (
                  <li key={i}>
                    <strong>{act.label}</strong>: {act.description}
                  </li>
                ))}
              </ul>
              {report.safe_next_actions.length === 0 && <p className="text-sm text-green-700">None recommended.</p>}
            </section>

            <section className="bg-red-50 p-6 shadow rounded-lg border border-red-200">
              <h2 className="text-lg font-bold text-red-800 mb-3">REQUIRES APPROVAL</h2>
              <ul className="list-disc pl-5 text-red-900 space-y-1 text-sm">
                {report.requires_approval.map((req, i) => (
                  <li key={i}>{req}</li>
                ))}
              </ul>
              {report.requires_approval.length === 0 && <p className="text-sm text-red-700">None identified.</p>}
            </section>
          </div>

          {report.runbook_reference && (
            <section className="bg-gray-800 p-6 shadow rounded-lg text-gray-200">
              <h2 className="text-lg font-bold text-gray-100 mb-2 flex justify-between">
                <span>RUNBOOK: {report.runbook_reference.title}</span>
                <span className="text-xs text-gray-400 font-normal">Match score: {(report.runbook_reference.score * 100).toFixed(0)}%</span>
              </h2>
              <p className="text-sm text-gray-400 mb-3 font-mono">{report.runbook_reference.path}</p>
              <pre className="bg-gray-900 p-4 rounded text-sm overflow-x-auto text-green-400 font-mono">
                {report.runbook_reference.relevant_snippet}
              </pre>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
