import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ManualTriggerForm } from "@/components/forms/manual-trigger";

export default async function SettingsPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const resolvedParams = await params;
  
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Workspace Settings</h1>
        <p className="text-gray-500 mt-1">Manage billing, database connections, and manual triggers.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-8">
          <Card>
            <CardHeader>
              <CardTitle>Billing & Subscription</CardTitle>
              <CardDescription>Your current plan and usage.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg bg-gray-50">
                <div>
                  <p className="font-semibold text-gray-900">Pro Plan</p>
                  <p className="text-sm text-gray-500">Billed monthly via Stripe</p>
                </div>
                <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Active (Mock)</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Registered Databases</CardTitle>
              </div>
              <CardDescription>Instances configured in the Instance Registry.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Instance ID</TableHead>
                    <TableHead>Engine</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">db-prod-01</TableCell>
                    <TableCell>PostgreSQL</TableCell>
                    <TableCell><Badge variant="outline" className="text-green-600 border-green-200">Connected</Badge></TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">db-analytics-02</TableCell>
                    <TableCell>PostgreSQL</TableCell>
                    <TableCell><Badge variant="outline" className="text-green-600 border-green-200">Connected</Badge></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        <div>
          <ManualTriggerForm tenantId={resolvedParams.tenantId} />
        </div>
      </div>
    </div>
  );
}
