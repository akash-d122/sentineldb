"use client";

import * as React from "react";
import { ChevronsUpDown, Plus } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
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
      <DropdownMenuTrigger className="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500">
        <span className="truncate">{activeTenant?.name}</span>
        <ChevronsUpDown className="w-4 h-4 ml-2 text-gray-400" />
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="start">
        <DropdownMenuLabel>Workspaces</DropdownMenuLabel>
        {tenants.map((tenant) => (
          <DropdownMenuItem 
            key={tenant.id}
            onClick={() => router.push(`/t/${tenant.id}/incidents`)}
          >
            {tenant.name}
            {tenant.id === currentTenantId && (
              <DropdownMenuShortcut>✓</DropdownMenuShortcut>
            )}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => router.push("/onboarding")}>
          <Plus className="w-4 h-4 mr-2" />
          Create Workspace
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
