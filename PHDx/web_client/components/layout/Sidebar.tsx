"use client";

import { useAppStore, ModuleType } from "@/stores/app-store";
import { cn } from "@/lib/utils";
import {
  PenLine,
  BarChart3,
  Network,
  Library,
  ClipboardCheck,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";

interface NavItem {
  id: ModuleType;
  label: string;
  icon: React.ReactNode;
  color: string;
  description: string;
}

const navItems: NavItem[] = [
  {
    id: "writing",
    label: "Writing Desk",
    icon: <PenLine className="w-5 h-5" />,
    color: "module-writing",
    description: "AI-assisted drafting",
  },
  {
    id: "data",
    label: "Data Lab",
    icon: <BarChart3 className="w-5 h-5" />,
    color: "module-data",
    description: "Analyze research data",
  },
  {
    id: "narrative",
    label: "Narrative",
    icon: <Network className="w-5 h-5" />,
    color: "module-narrative",
    description: "Structure & arguments",
  },
  {
    id: "library",
    label: "Library",
    icon: <Library className="w-5 h-5" />,
    color: "module-library",
    description: "Citations & Zotero",
  },
  {
    id: "auditor",
    label: "Auditor",
    icon: <ClipboardCheck className="w-5 h-5" />,
    color: "module-auditor",
    description: "Oxford Brookes criteria",
  },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar, activeModule, setActiveModule, apiConnected } =
    useAppStore();

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          "sidebar h-screen flex flex-col",
          sidebarCollapsed && "collapsed"
        )}
      >
        {/* Logo */}
        <div className="p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent-primary flex items-center justify-center flex-shrink-0">
            <Zap className="w-5 h-5 text-white" />
          </div>
          {!sidebarCollapsed && (
            <div className="animate-fade-in">
              <h1 className="text-lg font-semibold text-text-primary">PHDx</h1>
              <p className="text-xs text-text-tertiary">Thesis Command Center</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = activeModule === item.id;

            const button = (
              <button
                key={item.id}
                onClick={() => setActiveModule(item.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-150",
                  "text-text-secondary hover:text-text-primary hover:bg-bg-hover",
                  isActive && `bg-${item.color}-soft text-${item.color}`,
                  sidebarCollapsed && "justify-center px-2"
                )}
                style={
                  isActive
                    ? {
                        backgroundColor: `var(--${item.color}-soft)`,
                        color: `var(--${item.color})`,
                      }
                    : undefined
                }
              >
                <span className="flex-shrink-0">{item.icon}</span>
                {!sidebarCollapsed && (
                  <span className="text-sm font-medium animate-fade-in">
                    {item.label}
                  </span>
                )}
              </button>
            );

            if (sidebarCollapsed) {
              return (
                <Tooltip key={item.id}>
                  <TooltipTrigger asChild>{button}</TooltipTrigger>
                  <TooltipContent side="right">
                    <p className="font-medium">{item.label}</p>
                    <p className="text-text-tertiary">{item.description}</p>
                  </TooltipContent>
                </Tooltip>
              );
            }

            return button;
          })}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-border">
          {/* Connection status */}
          <div
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-lg mb-2",
              sidebarCollapsed && "justify-center px-2"
            )}
          >
            <span
              className={cn(
                "w-2 h-2 rounded-full flex-shrink-0",
                apiConnected ? "bg-success" : "bg-text-tertiary"
              )}
            />
            {!sidebarCollapsed && (
              <span className="text-xs text-text-secondary animate-fade-in">
                {apiConnected ? "Connected" : "Offline"}
              </span>
            )}
          </div>

          {/* Collapse toggle */}
          <button
            onClick={toggleSidebar}
            className={cn(
              "w-full flex items-center gap-2 px-3 py-2 rounded-lg",
              "text-text-tertiary hover:text-text-primary hover:bg-bg-hover transition-colors",
              sidebarCollapsed && "justify-center px-2"
            )}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <>
                <ChevronLeft className="w-4 h-4" />
                <span className="text-xs">Collapse</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </TooltipProvider>
  );
}
