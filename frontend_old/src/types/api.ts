export type Severity = "P1" | "P2" | "P3" | "P4";
export type IncidentStatus = "queued" | "collecting" | "analyzing" | "report_ready" | "failed";
export type EvidenceStatus = "OK" | "WARN" | "CRITICAL" | "UNAVAILABLE";
export type RCAStrength = "High" | "Medium" | "Low";

export interface Incident {
  incident_id: string;
  instance_id: string;
  alert_type: string;
  severity: Severity;
  metric_value: number | null;
  threshold_value: number | null;
  triggered_at: string;
  status: IncidentStatus;
  created_at: string;
}

export interface EvidenceItem {
  id: string;
  source: string;
  label: string;
  value: string | number | null;
  unit: string | null;
  timestamp: string;
  status: EvidenceStatus;
  raw_reference: string | null;
  display_text: string;
}

export interface RunbookMatch {
  path: string;
  title: string;
  relevant_snippet: string;
  score: number;
}

export interface SafeAction {
  label: string;
  description: string;
  catalog_key: string;
}

export interface IncidentReport {
  report_id: string;
  incident_id: string;
  rca_strength: RCAStrength;
  root_cause_summary: string;
  why_most_likely: string[];
  evidence: EvidenceItem[];
  runbook_reference: RunbookMatch | null;
  safe_next_actions: SafeAction[];
  requires_approval: string[];
  missing_evidence: string[];
  llm_used: boolean;
  generated_at: string;
}
