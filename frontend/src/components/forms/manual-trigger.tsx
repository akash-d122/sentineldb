"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { triggerManualAnalysis } from "@/app/actions";

export function ManualTriggerForm({ tenantId }: { tenantId: string }) {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      const formData = new FormData(e.currentTarget);
      await triggerManualAnalysis(formData);
      toast.success("Analysis triggered successfully", {
        description: "The background worker is now gathering evidence."
      });
      // Optionally reset form
      e.currentTarget.reset();
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Failed to trigger analysis");
    } finally {
      setLoading(false);
    }
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
            <Input required name="instance_id" placeholder="e.g. db-prod-01" />
          </div>
          <div className="space-y-2">
            <Label>Alert Focus</Label>
            <Select required name="alert_type" defaultValue="high_cpu">
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
              <Input type="number" name="time_window" required defaultValue="30" />
            </div>
            <div className="space-y-2">
              <Label>Severity</Label>
              <Select required name="severity" defaultValue="P2">
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
