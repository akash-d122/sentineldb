"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { RegisterDbForm } from "@/components/forms/register-db";
import { Badge } from "@/components/ui/badge";

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [tenantName, setTenantName] = useState("");
  const [tenantId, setTenantId] = useState("");

  const handleCreateTenant = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate creating a tenant
    setTenantId("t-12345");
    setStep(2);
  };

  if (step === 2) {
    return <RegisterDbForm tenantId={tenantId} />;
  }

  return (
    <Card>
      <form onSubmit={handleCreateTenant}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Create Workspace</CardTitle>
            <Badge variant="secondary">Pro Plan (Mocked)</Badge>
          </div>
          <CardDescription>Name your workspace to get started.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="workspace">Workspace Name</Label>
            <Input 
              id="workspace" 
              placeholder="Acme Corp" 
              required 
              value={tenantName}
              onChange={(e) => setTenantName(e.target.value)}
            />
          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full">Continue</Button>
        </CardFooter>
      </form>
    </Card>
  );
}
