import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ShieldAlert, BookOpen, AlertTriangle } from "lucide-react";
import type { IncidentReport } from "@/types/api";

export function RcaSummary({ report }: { report: IncidentReport }) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card className="md:col-span-2 border-l-4 border-l-red-500">
        <CardHeader>
          <CardTitle className="text-lg flex items-center justify-between">
            <span>Root Cause</span>
            <Badge variant="destructive">Strength: {report.rca_strength}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-800 text-lg">{report.root_cause_summary}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-md flex items-center">
            <ShieldAlert className="w-4 h-4 mr-2 text-blue-600" />
            Why This Is Most Likely
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc pl-5 space-y-2 text-gray-600">
            {report.why_most_likely.map((reason, i) => (
              <li key={i}>{reason}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-md flex items-center">
            <BookOpen className="w-4 h-4 mr-2 text-green-600" />
            Safe Next Actions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {report.safe_next_actions.map((action, i) => (
              <li key={i} className="flex gap-2">
                <span className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-800 text-xs font-bold">
                  {i + 1}
                </span>
                <div>
                  <p className="font-medium text-gray-900">{action.label}</p>
                  <p className="text-sm text-gray-500">{action.description}</p>
                </div>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {report.requires_approval.length > 0 && (
        <Card className="md:col-span-2 bg-orange-50 border-orange-200">
          <CardHeader>
            <CardTitle className="text-md flex items-center text-orange-800">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Requires DBE Approval
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc pl-5 space-y-1 text-orange-700">
              {report.requires_approval.map((req, i) => (
                <li key={i}>{req}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
