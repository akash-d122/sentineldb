"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { buttonVariants } from "@/components/ui/button";
import Link from "next/link";

interface Incident {
  incident_id: string;
  instance_id: string;
  alert_type: string;
  severity: string;
  status: string;
  triggered_at?: string;
}

export function IncidentFeedLive({ 
  tenantId, 
  initialIncidents 
}: { 
  tenantId: string; 
  initialIncidents: Incident[] 
}) {
  const [incidents, setIncidents] = useState<Incident[]>(initialIncidents);

  useEffect(() => {
    // Connect to the Next.js API route which securely proxies the FastAPI SSE endpoint
    const eventSource = new EventSource('/api/stream');

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'initial_state') {
          // If we receive the full recent array from the backend
          // We can optionally merge it, but for now we just rely on initialIncidents from SSR
        } else if (data.incident_id && data.status) {
          // We received an individual status update
          setIncidents(current => {
            const exists = current.some(i => i.incident_id === data.incident_id);
            if (exists) {
              return current.map(i => 
                i.incident_id === data.incident_id 
                  ? { ...i, status: data.status } 
                  : i
              );
            } else {
              // Wait for a full page refresh for entirely new incidents, or we could fetch it.
              // For MVP, we just update existing ones.
              return current;
            }
          });
        }
      } catch (err) {
        console.error("Failed to parse SSE message", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE connection error", err);
      // EventSource auto-reconnects, but we can close it if we wanted to
    };

    return () => {
      eventSource.close();
    };
  }, []);

  if (incidents.length === 0) {
    return (
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
    );
  }

  return (
    <>
      {incidents.map((inc) => {
        const isReady = inc.status === 'report_ready';
        const isFailed = inc.status === 'failed';
        const statusColor = isReady ? 'bg-emerald-500' : isFailed ? 'bg-red-500' : 'bg-blue-500 animate-pulse';
        const statusText = inc.status ? inc.status.replace(/_/g, ' ') : 'unknown';

        let formattedTime = 'Invalid date';
        if (inc.triggered_at) {
          const d = new Date(inc.triggered_at);
          if (!isNaN(d.getTime())) {
            formattedTime = d.toISOString().substring(11, 16);
          }
        }

        return (
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
                <span className={`w-2 h-2 rounded-full ${statusColor}`} />
                <span className="text-sm text-gray-700 capitalize">{statusText}</span>
              </div>
            </TableCell>
            <TableCell className="text-gray-500 text-sm">
              {formattedTime}
            </TableCell>
            <TableCell className="text-right">
              <Link
                className={buttonVariants({ variant: "ghost", size: "sm", className: "opacity-0 group-hover:opacity-100 transition-opacity text-blue-600 hover:text-blue-700 hover:bg-blue-50" })}
                href={`/t/${tenantId}/incidents/${inc.incident_id}`}
              >
                View Report &rarr;
              </Link>
            </TableCell>
          </TableRow>
        );
      })}
    </>
  );
}
