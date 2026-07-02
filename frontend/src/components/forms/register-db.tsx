"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useRouter } from "next/navigation";
import { registerDatabase } from "@/app/actions";
import { toast } from "sonner";
import { useFeatureFlagEnabled, usePostHog } from 'posthog-js/react';
import { LockIcon } from "lucide-react";


export function RegisterDbForm({ tenantId }: { tenantId: string }) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const posthog = usePostHog();
  
  // A/B Test Flag
  const isSecurityEnhanced = useFeatureFlagEnabled('experiment-db-connection-security');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      const formData = new FormData(e.currentTarget);
      await registerDatabase(formData);
      
      // Capture success event for A/B testing conversion tracking
      posthog?.capture('database_connected_success', {
        tenant_id: tenantId,
        engine: formData.get("engine"),
        variant: isSecurityEnhanced ? 'security_enhanced' : 'control'
      });
      
      toast.success("Database connected successfully");

      router.push(`/t/${tenantId}/incidents`);
    } catch (error: Error | unknown) {
      console.error(error);
      toast.error((error as Error).message || "Failed to connect database");
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>

      <Card>
        <CardHeader>
          <CardTitle>
            {isSecurityEnhanced ? "Securely Connect your Database" : "Connect your Database"}
          </CardTitle>
          <CardDescription>
            {isSecurityEnhanced ? (
              <span className="flex flex-col gap-2 mt-1">
                <span>SentinelDB uses an encrypted, read-only connection. We never execute DML/DDL or store your raw table data.</span>
                <a href="#" className="text-sm font-medium text-blue-600 hover:underline">Read our Security Architecture & Guardrails &rarr;</a>
              </span>
            ) : "We need read-only access to monitor incidents."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">

          <div className="space-y-2">
            <Label>Engine</Label>
            <Select required name="engine" defaultValue="postgresql">
              <SelectTrigger>
                <SelectValue placeholder="Select engine" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="postgresql">PostgreSQL</SelectItem>
                <SelectItem value="mysql">MySQL</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="host">Host</Label>
              <Input id="host" name="host" required placeholder="db.example.com" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="port">Port</Label>
              <Input id="port" name="port" required placeholder="5432" />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="database">Database Name</Label>
            <Input id="database" name="database" required placeholder="postgres" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="username">Read-only Username</Label>
            <Input id="username" name="username" required placeholder="sentinel_ro" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="flex items-center gap-1.5">
              Password {isSecurityEnhanced && <LockIcon className="w-3.5 h-3.5 text-emerald-600" />}
            </Label>
            <Input id="password" name="password" required type="password" />

          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Connecting..." : "Connect Database"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
