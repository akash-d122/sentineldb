import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/utils/supabase/server";

export async function GET(request: NextRequest) {
  const supabase = await createClient();
  const session = await supabase.auth.getSession();
  const token = session.data.session?.access_token;

  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  try {
    const res = await fetch(`${API_BASE}/incidents/stream`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "text/event-stream",
      },
      // Using duplex: 'half' or similar isn't strictly needed for GET,
      // but caching must be disabled to stream properly.
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json({ error: "Failed to connect to stream" }, { status: res.status });
    }

    // Return the response directly, which will stream the events back to the client
    return new Response(res.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  } catch (error) {
    console.error("Stream proxy error:", error);
    return NextResponse.json({ error: "Stream connection failed" }, { status: 500 });
  }
}
