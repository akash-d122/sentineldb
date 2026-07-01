"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { TenantSwitcher } from "./tenant-switcher";
import { Activity, Settings, LayoutDashboard, History, DatabaseZap } from "lucide-react";
import { cn } from "@/lib/utils";

export function Sidebar({ tenantId }: { tenantId: string }) {
  const pathname = usePathname();

  const navigation = [
    { name: "Live Feed", href: `/t/${tenantId}/incidents`, icon: Activity },
    { name: "Historical", href: `/t/${tenantId}/historical`, icon: History },
    { name: "Settings", href: `/t/${tenantId}/settings`, icon: Settings },
  ];

  return (
    <div className="flex flex-col w-72 border-r border-gray-100 bg-[#FAFAFA] h-screen">
      <div className="p-6">
        <h1 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
            <DatabaseZap className="w-4 h-4" />
          </div>
          SentinelDB
        </h1>
        <TenantSwitcher currentTenantId={tenantId} />
      </div>
      
      <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2.5 text-sm font-medium rounded-xl group transition-all duration-200",
                isActive 
                  ? "bg-white text-blue-700 shadow-sm border border-gray-100/50" 
                  : "text-gray-600 hover:bg-white/60 hover:text-gray-900 border border-transparent"
              )}
            >
              <item.icon 
                className={cn(
                  "w-4 h-4 mr-3 flex-shrink-0 transition-colors",
                  isActive ? "text-blue-600" : "text-gray-400 group-hover:text-gray-500"
                )} 
              />
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      <div className="p-4 m-4 rounded-xl bg-white border border-gray-100 shadow-sm flex items-center">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-100 to-blue-50 text-blue-700 flex items-center justify-center font-bold text-sm border border-blue-100">
          DB
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium text-gray-900">DBE Admin</p>
          <p className="text-xs text-gray-500">Pro Plan</p>
        </div>
      </div>
    </div>
  );
}
