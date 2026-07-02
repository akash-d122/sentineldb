import { redirect } from "next/navigation";
import { createClient } from "@/utils/supabase/server";

export default async function Home() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const { data: { session } } = await supabase.auth.getSession();
  
  let tenantId = user.id;
  if (session) {
    try {
      const payload = JSON.parse(Buffer.from(session.access_token.split('.')[1], 'base64').toString());
      if (payload.tenant_id) {
        tenantId = payload.tenant_id;
      }
    } catch (e) {
      console.error("Failed to parse JWT", e);
    }
  }

  redirect(`/t/${tenantId}/incidents`);
}
