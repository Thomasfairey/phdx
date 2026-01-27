"use client";

import { useAppStore } from "@/stores/app-store";
import { Button } from "@/components/ui/button";
import { Search, Command, Settings } from "lucide-react";

const moduleLabels = {
  writing: "Writing Desk",
  data: "Data Lab",
  narrative: "Narrative Intelligence",
  library: "Library",
  auditor: "Brookes Auditor",
};

const moduleDescriptions = {
  writing: "AI-assisted drafting with your voice",
  data: "Upload, analyze, and visualize research data",
  narrative: "Structure analysis and argument mapping",
  library: "Zotero citations and bibliography",
  auditor: "Oxford Brookes criteria evaluation",
};

export function Header() {
  const { activeModule } = useAppStore();

  return (
    <header className="h-header border-b border-border bg-bg-primary px-6 flex items-center justify-between">
      {/* Module title */}
      <div>
        <h2 className="text-lg font-semibold text-text-primary">
          {moduleLabels[activeModule]}
        </h2>
        <p className="text-sm text-text-secondary">
          {moduleDescriptions[activeModule]}
        </p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {/* Command palette trigger */}
        <Button
          variant="ghost"
          size="sm"
          className="gap-2 text-text-secondary"
        >
          <Search className="w-4 h-4" />
          <span className="hidden sm:inline">Search</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium bg-bg-tertiary rounded border border-border">
            <Command className="w-3 h-3" />K
          </kbd>
        </Button>

        {/* Settings */}
        <Button variant="ghost" size="icon" className="text-text-secondary">
          <Settings className="w-4 h-4" />
        </Button>
      </div>
    </header>
  );
}
