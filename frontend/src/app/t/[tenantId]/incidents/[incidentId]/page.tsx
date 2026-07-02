import { buttonVariants } from "@/components/ui/button";
import { EvidencePanel } from "@/components/incidents/evidence-panel";
import { RcaSummary } from "@/components/incidents/rca-summary";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import type { IncidentReport } from "@/types/api";
import { createClient } from "@/utils/supabase/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function getIncidentReport(incidentId: string): Promise<{ report: IncidentReport | null, error: string | null }> {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return { report: null, error: "Unauthorized" };
  }

  try {
    const { data: { session } } = await supabase.auth.getSession();
    const res = await fetch(`${API_BASE}/incidents/${incidentId}/report`, {
      headers: { Authorization: `Bearer ${session?.access_token}` },
      cache: "no-store",
    });

    if (!res.ok) {
      if (res.status === 404) {
        return { report: null, error: "Report not found or not ready yet." };
      }
      return { report: null, error: `API Error: ${res.statusText}` };
    }

    const data = await res.json();
    return { report: data, error: null };
  } catch (error: any) {
    console.error(`Failed to fetch report for incident ${incidentId}`, error);
    return { report: null, error: error.message || "Failed to fetch report" };
  }
}

export default async function IncidentDetailPage({ 
  params 
}: { 
  params: Promise<{ tenantId: string, incidentId: string }> 
}) {
  const resolvedParams = await params;
  const { report, error } = await getIncidentReport(resolvedParams.incidentId);
  
  if (error || !report) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link className={buttonVariants({ variant: "ghost", size: "icon" })} href={`/t/${resolvedParams.tenantId}/incidents`}>
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Incident {resolvedParams.incidentId}</h1>
          </div>
        </div>
        <div className="p-8 text-center text-red-500 bg-red-50 rounded-2xl">
          <p>{error || "Report not available"}</p>
        </div>
      </div>
    );
  }

  let formattedTime = 'Invalid date';
  if (report.generated_at) {
    const d = new Date(report.generated_at);
    if (!isNaN(d.getTime())) {
      formattedTime = d.toISOString().substring(0, 19).replace('T', ' ') + ' UTC';
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      <div className="flex items-center gap-4">
        <Link className={buttonVariants({ variant: "ghost", size: "icon" })} href={`/t/${resolvedParams.tenantId}/incidents`}>
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Incident {resolvedParams.incidentId}</h1>
          <p className="text-gray-500 mt-1">Generated at {formattedTime}</p>
        </div>
        <div className="ml-auto">
          <EvidencePanel evidence={report.evidence} />
        </div>
      </div>

      <RcaSummary report={report} />
    </div>
  );
}
