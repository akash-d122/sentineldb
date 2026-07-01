import { Sidebar } from "@/components/navigation/sidebar";

export default async function TenantLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ tenantId: string }>;
}) {
  const resolvedParams = await params;
  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <Sidebar tenantId={resolvedParams.tenantId} />
      <main className="flex-1 overflow-y-auto">
        <div className="p-8 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
