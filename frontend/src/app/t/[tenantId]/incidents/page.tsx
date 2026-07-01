import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Link from "next/link";
import { createClient } from "@/utils/supabase/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function getIncidents() {
  const supabase = await createClient();
  const { data: { session } } = await supabase.auth.getSession();
  
  if (!session) return [];

  try {
    const res = await fetch(`${API_BASE}/incidents`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
      next: { revalidate: 10 } // Cache for 10 seconds for standard stale-while-revalidate
    });
    if (!res.ok) return [];
    return res.json();
  } catch (error) {
    console.error("Failed to fetch incidents", error);
    return [];
  }
}

export default async function IncidentsPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const resolvedParams = await params;
  const incidents = await getIncidents();

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="space-y-1">
          <h1 className="text-4xl font-semibold tracking-tight text-gray-900">Live Incidents</h1>
          <p className="text-gray-500 text-sm">Real-time alerts and RCA status across your instances.</p>
        </div>
        <Link className={buttonVariants({ variant: "default", className: "shadow-sm rounded-full px-6" })} href={`/t/${resolvedParams.tenantId}/settings`}>
          Manual Trigger
        </Link>
      </div>

      <Card className="overflow-hidden border-gray-100 shadow-sm rounded-2xl">
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-gray-50/50">
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[180px] font-medium text-gray-600">Instance</TableHead>
                <TableHead className="font-medium text-gray-600">Alert Type</TableHead>
                <TableHead className="font-medium text-gray-600">Severity</TableHead>
                <TableHead className="font-medium text-gray-600">Status</TableHead>
                <TableHead className="font-medium text-gray-600">Time</TableHead>
                <TableHead className="text-right font-medium text-gray-600">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {incidents.map((inc: any) => (
                <TableRow key={inc.incident_id} className="group transition-colors">
                  <TableCell className="font-medium text-gray-900">{inc.instance_id}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-100/50 text-gray-600 text-xs font-mono">
                      {inc.alert_type}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={`
                      font-medium px-2 py-0.5 border-transparent
                      ${inc.severity === 'P1' ? 'bg-red-50 text-red-700' : 'bg-orange-50 text-orange-700'}
                    `}>
                      {inc.severity}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${inc.status === 'report_ready' ? 'bg-emerald-500' : 'bg-blue-500 animate-pulse'}`} />
                      <span className="text-sm text-gray-700 capitalize">{inc.status.replace('_', ' ')}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-gray-500 text-sm">
                    {new Date(inc.triggered_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </TableCell>
                  <TableCell className="text-right">
                    <Link 
                      className={buttonVariants({ variant: "ghost", size: "sm", className: "opacity-0 group-hover:opacity-100 transition-opacity text-blue-600 hover:text-blue-700 hover:bg-blue-50" })} 
                      href={`/t/${resolvedParams.tenantId}/incidents/${inc.incident_id}`}
                    >
                      View Report &rarr;
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
              {incidents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center text-gray-400">
                    <div className="flex flex-col items-center justify-center space-y-1">
                      <div className="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center mb-2">
                        <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <p>No active incidents.</p>
                      <p className="text-xs">Your databases are healthy.</p>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
