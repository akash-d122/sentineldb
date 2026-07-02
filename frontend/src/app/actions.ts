"use server";

import { createClient } from "@/utils/supabase/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function registerDatabase(formData: FormData) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error("Unauthorized");
  const session = await supabase.auth.getSession();
  const token = session.data.session?.access_token;

  const payload = {
    engine: formData.get("engine"),
    host: formData.get("host"),
    port: parseInt(formData.get("port") as string, 10),
    database: formData.get("database"),
    username: formData.get("username"),
    password: formData.get("password"),
  };

  const res = await fetch(`${API_BASE}/tenant/instances`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Failed to register database: ${res.statusText} - ${errorText}`);
  }

  return await res.json();
}

export async function triggerManualAnalysis(formData: FormData) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error("Unauthorized");
  const session = await supabase.auth.getSession();
  const token = session.data.session?.access_token;

  const payload = {
    instance_id: formData.get("instance_id"),
    alert_type: formData.get("alert_type"),
    severity: formData.get("severity"),
  };

  const res = await fetch(`${API_BASE}/incidents/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Failed to trigger analysis: ${res.statusText} - ${errorText}`);
  }

  return await res.json();
}
