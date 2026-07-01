import { buttonVariants } from "@/components/ui/button";
import { EvidencePanel } from "@/components/incidents/evidence-panel";
import { RcaSummary } from "@/components/incidents/rca-summary";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import type { IncidentReport, EvidenceItem } from "@/types/api";

// Mock data
const mockReport: IncidentReport = {
  report_id: "rep-123",
  incident_id: "inc-1",
  rca_strength: "High",
  root_cause_summary: "Connection saturation is the most likely cause of high DB CPU. Active connections reached 423/500 while slow query volume spiked on the orders query path.",
  why_most_likely: [
    "CPU and connection spike happened in the same 10-minute window.",
    "Slow query evidence points to repeated expensive reads, not replication or disk failure.",
    "Replication lag was normal, so replica delay is unlikely to be the primary cause."
  ],
  evidence: [
    {
      id: "ev-1",
      source: "cloudwatch",
      label: "CPU Utilization",
      value: 91.3,
      unit: "%",
      timestamp: new Date().toISOString(),
      status: "CRITICAL",
      raw_reference: null,
      display_text: ""
    },
    {
      id: "ev-2",
      source: "db",
      label: "Active Connections",
      value: 423,
      unit: "sessions",
      timestamp: new Date().toISOString(),
      status: "CRITICAL",
      raw_reference: null,
      display_text: ""
    }
  ],
  runbook_reference: {
    title: "High CPU - Connection Saturation",
    path: "runbooks/high_cpu_connection_saturation.md",
    relevant_snippet: "",
    score: 0.95
  },
  safe_next_actions: [
    {
      label: "Check active sessions",
      description: "Run approved active-session diagnostic query.",
      catalog_key: "check_active_sessions"
    },
    {
      label: "Explain top query",
      description: "Run approved EXPLAIN diagnostic query for the flagged query fingerprint.",
      catalog_key: "explain_query"
    }
  ],
  requires_approval: [
    "Killing sessions.",
    "Adding indexes.",
    "Restarting DB or application services."
  ],
  missing_evidence: [],
  llm_used: true,
  generated_at: new Date().toISOString()
};

export default async function IncidentDetailPage({ 
  params 
}: { 
  params: Promise<{ tenantId: string, incidentId: string }> 
}) {
  const resolvedParams = await params;
  
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link className={buttonVariants({ variant: "ghost", size: "icon" })} href={`/t/${resolvedParams.tenantId}/incidents`}>
          
            <ArrowLeft className="w-5 h-5" />
          
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Incident {resolvedParams.incidentId}</h1>
          <p className="text-gray-500 mt-1">Generated at {new Date(mockReport.generated_at).toLocaleString()}</p>
        </div>
        <div className="ml-auto">
          <EvidencePanel evidence={mockReport.evidence} />
        </div>
      </div>

      <RcaSummary report={mockReport} />
    </div>
  );
}
