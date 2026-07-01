"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { TenantSwitcher } from "./tenant-switcher";
import { Activity, Settings, LayoutDashboard, History } from "lucide-react";
import { cn } from "@/lib/utils";

export function Sidebar({ tenantId }: { tenantId: string }) {
  const pathname = usePathname();

  const navigation = [
    { name: "Live Feed", href: `/t/${tenantId}/incidents`, icon: Activity },
    { name: "Historical", href: `/t/${tenantId}/historical`, icon: History },
    { name: "Settings", href: `/t/${tenantId}/settings`, icon: Settings },
  ];

  return (
    <div className="flex flex-col w-64 border-r border-gray-200 bg-gray-50 h-screen">
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <LayoutDashboard className="w-5 h-5 text-blue-600" />
          SentinelDB
        </h1>
        <TenantSwitcher currentTenantId={tenantId} />
      </div>
      
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md group",
                isActive 
                  ? "bg-blue-50 text-blue-700" 
                  : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              <item.icon 
                className={cn(
                  "w-5 h-5 mr-3 flex-shrink-0",
                  isActive ? "text-blue-700" : "text-gray-400 group-hover:text-gray-500"
                )} 
              />
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
            DB
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-700">DBE Admin</p>
            <p className="text-xs text-gray-500">Pro Plan</p>
          </div>
        </div>
      </div>
    </div>
  );
}
