"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

export function ManualTriggerForm({ tenantId }: { tenantId: string }) {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    
    // Simulate API call to FastAPI manual trigger endpoint
    setTimeout(() => {
      setLoading(false);
      toast.success("Analysis triggered successfully", {
        description: "The background worker is now gathering evidence."
      });
    }, 800);
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader>
          <CardTitle>Manual Analysis Trigger</CardTitle>
          <CardDescription>Force an RCA run for a specific database instance and alert type.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Instance ID</Label>
            <Input required placeholder="e.g. db-prod-01" />
          </div>
          <div className="space-y-2">
            <Label>Alert Focus</Label>
            <Select required defaultValue="high_cpu">
              <SelectTrigger>
                <SelectValue placeholder="Select alert type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="high_cpu">High CPU</SelectItem>
                <SelectItem value="slow_query">Slow Query Spike</SelectItem>
                <SelectItem value="replication_lag">Replication Lag</SelectItem>
                <SelectItem value="db_unreachable">DB Unreachable</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Time Window (Minutes)</Label>
              <Input type="number" required defaultValue="30" />
            </div>
            <div className="space-y-2">
              <Label>Severity</Label>
              <Select required defaultValue="P2">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="P1">P1</SelectItem>
                  <SelectItem value="P2">P2</SelectItem>
                  <SelectItem value="P3">P3</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={loading}>
            {loading ? "Triggering..." : "Run Analysis"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
