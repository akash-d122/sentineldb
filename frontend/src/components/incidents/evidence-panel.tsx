"use client";

import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FileBarChart } from "lucide-react";
import type { EvidenceItem } from "@/types/api";

export function EvidencePanel({ evidence }: { evidence: EvidenceItem[] }) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="w-full sm:w-auto">
          <FileBarChart className="w-4 h-4 mr-2" />
          View Raw Evidence
        </Button>
      </SheetTrigger>
      <SheetContent className="w-full sm:max-w-md overflow-y-auto">
        <SheetHeader className="mb-6">
          <SheetTitle>Raw Evidence</SheetTitle>
          <SheetDescription>
            Telemetry and query logs collected during the incident window.
          </SheetDescription>
        </SheetHeader>
        
        <div className="space-y-6">
          {evidence.map((item) => (
            <div key={item.id} className="border rounded-lg p-4 bg-gray-50">
              <div className="flex justify-between items-start mb-2">
                <div className="font-semibold text-gray-900">{item.label}</div>
                <Badge variant={item.status === 'OK' ? 'secondary' : 'destructive'}>
                  {item.status}
                </Badge>
              </div>
              <div className="text-sm text-gray-500 mb-2">
                Source: <span className="font-mono bg-gray-200 px-1 rounded">{item.source}</span>
              </div>
              <div className="text-sm">
                <span className="font-medium">Value:</span> {item.value} {item.unit}
              </div>
              {item.raw_reference && (
                <div className="mt-3 bg-gray-900 text-gray-100 p-3 rounded-md text-xs font-mono overflow-x-auto">
                  {item.raw_reference}
                </div>
              )}
            </div>
          ))}
        </div>
      </SheetContent>
    </Sheet>
  );
}
