import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { createClient } from "@/utils/supabase/server";

async function getIncidents() {
  // In a real app, this would fetch from the FastAPI backend using the JWT
  // const supabase = await createClient();
  // const { data: { session } } = await supabase.auth.getSession();
  // const res = await fetch('http://localhost:8000/api/v1/incidents', {
  //   headers: { Authorization: `Bearer ${session?.access_token}` }
  // });
  // return res.json();
  
  // Mock data for UI development
  return [
    {
      incident_id: "inc-1",
      instance_id: "db-prod-01",
      alert_type: "high_cpu",
      severity: "P1",
      status: "report_ready",
      triggered_at: new Date().toISOString(),
    },
    {
      incident_id: "inc-2",
      instance_id: "db-analytics-02",
      alert_type: "slow_query",
      severity: "P3",
      status: "analyzing",
      triggered_at: new Date(Date.now() - 3600000).toISOString(),
    }
  ];
}

export default async function IncidentsPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const resolvedParams = await params;
  const incidents = await getIncidents();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Live Incident Feed</h1>
          <p className="text-gray-500 mt-1">Real-time alerts and RCA status.</p>
        </div>
        <Link className={buttonVariants({ variant: "default" })} href={`/t/${resolvedParams.tenantId}/settings`}>
          Manual Trigger
        </Link>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Instance</TableHead>
                <TableHead>Alert Type</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Time</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {incidents.map((inc) => (
                <TableRow key={inc.incident_id}>
                  <TableCell className="font-medium">{inc.instance_id}</TableCell>
                  <TableCell>{inc.alert_type}</TableCell>
                  <TableCell>
                    <Badge variant={inc.severity === 'P1' ? 'destructive' : 'secondary'}>
                      {inc.severity}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={inc.status === 'report_ready' ? 'default' : 'outline'} className={inc.status === 'report_ready' ? 'bg-green-600' : ''}>
                      {inc.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-gray-500 text-sm">
                    {new Date(inc.triggered_at).toLocaleTimeString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <Link className={buttonVariants({ variant: "ghost", size: "sm" })} href={`/t/${resolvedParams.tenantId}/incidents/${inc.incident_id}`}>
                      View Report
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
              {incidents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-gray-500">
                    No active incidents.
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
