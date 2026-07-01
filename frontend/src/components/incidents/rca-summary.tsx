import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ShieldAlert, BookOpen, AlertTriangle, Zap, CheckCircle2 } from "lucide-react";
import type { IncidentReport } from "@/types/api";

export function RcaSummary({ report }: { report: IncidentReport }) {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      {/* Root Cause (Full width or 2/3) */}
      <Card className="md:col-span-3 border-0 bg-gradient-to-br from-red-50 to-white shadow-sm overflow-hidden relative">
        <div className="absolute top-0 left-0 w-1 h-full bg-red-500" />
        <CardHeader className="pb-2">
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
                <Zap className="w-5 h-5 mr-2 text-red-500" />
                Root Cause Analysis
              </CardTitle>
              <CardDescription className="mt-1">Automatically determined based on deterministic rules and DB telemetry.</CardDescription>
            </div>
            <Badge variant="outline" className="bg-white border-red-200 text-red-700 font-semibold px-3 py-1">
              Confidence: {report.rca_strength}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-gray-900 text-lg leading-relaxed font-medium mt-2">{report.root_cause_summary}</p>
        </CardContent>
      </Card>

      {/* Why This Is Most Likely */}
      <Card className="md:col-span-2 border border-gray-100 shadow-sm rounded-2xl">
        <CardHeader>
          <CardTitle className="text-base font-semibold flex items-center text-gray-900">
            <ShieldAlert className="w-4 h-4 mr-2 text-blue-600" />
            Why This Is Most Likely
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-4">
            {report.why_most_likely.map((reason, i) => (
              <li key={i} className="flex gap-3 text-gray-600">
                <CheckCircle2 className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <span className="leading-relaxed">{reason}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Safe Next Actions */}
      <Card className="md:col-span-1 border border-gray-100 shadow-sm rounded-2xl bg-emerald-50/30">
        <CardHeader>
          <CardTitle className="text-base font-semibold flex items-center text-gray-900">
            <BookOpen className="w-4 h-4 mr-2 text-emerald-600" />
            Safe Next Actions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-4">
            {report.safe_next_actions.map((action, i) => (
              <li key={i} className="relative pl-6">
                <span className="absolute left-0 top-1 w-4 h-4 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-[10px] font-bold">
                  {i + 1}
                </span>
                <div>
                  <p className="font-semibold text-gray-900 text-sm">{action.label}</p>
                  <p className="text-sm text-gray-500 mt-1 leading-snug">{action.description}</p>
                </div>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Requires Approval (Warning) */}
      {report.requires_approval.length > 0 && (
        <Card className="md:col-span-3 bg-[#FFF9F2] border-[#FFE4C4] shadow-sm rounded-2xl">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center text-[#B25E09]">
              <AlertTriangle className="w-5 h-5 mr-2" />
              Requires DBE Approval
            </CardTitle>
            <CardDescription className="text-[#D97706]">
              SentinelDB never executes these actions automatically. Manual intervention is required.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {report.requires_approval.map((req, i) => (
                <div key={i} className="bg-white border border-[#FFE4C4] text-[#B25E09] px-3 py-1.5 rounded-lg text-sm font-medium shadow-sm">
                  {req}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
