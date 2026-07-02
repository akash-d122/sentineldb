"use client";

import * as React from "react";
import { ChevronsUpDown, Plus, Database } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useRouter } from "next/navigation";

export function TenantSwitcher({ currentTenantId }: { currentTenantId: string }) {
  const router = useRouter();

  // Mock tenants for UI
  const tenants = [
    { id: "t-12345", name: "Acme Corp" },
    { id: "t-67890", name: "Personal Project" }
  ];

  const activeTenant = tenants.find(t => t.id === currentTenantId) || tenants[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center justify-between w-full px-4 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-200/60 rounded-xl shadow-sm hover:bg-gray-50 hover:border-gray-200 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/20">
        <div className="flex items-center gap-2 truncate">
          <Database className="w-4 h-4 text-gray-400" />
          <span className="truncate">{activeTenant?.name}</span>
        </div>
        <ChevronsUpDown className="w-4 h-4 ml-2 text-gray-400" />
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64 rounded-xl p-2" align="start">
        <DropdownMenuLabel className="text-xs text-gray-400 uppercase tracking-wider font-semibold">Workspaces</DropdownMenuLabel>
        <div className="space-y-1 mt-1">
          {tenants.map((tenant) => (
            <DropdownMenuItem 
              key={tenant.id}
              onClick={() => router.push(`/t/${tenant.id}/incidents`)}
              className="rounded-lg cursor-pointer flex items-center justify-between"
            >
              {tenant.name}
              {tenant.id === currentTenantId && (
                <span className="text-blue-600 font-bold">✓</span>
              )}
            </DropdownMenuItem>
          ))}
        </div>
        <DropdownMenuSeparator className="my-2" />
        <DropdownMenuItem onClick={() => router.push("/onboarding")} className="rounded-lg cursor-pointer text-blue-600">
          <Plus className="w-4 h-4 mr-2" />
          Create Workspace
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
