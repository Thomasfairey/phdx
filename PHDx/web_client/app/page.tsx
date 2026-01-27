"use client";

import { useAppStore } from "@/stores/app-store";
import { Sidebar, Header } from "@/components/layout";
import { WritingDesk } from "@/components/writing";
import { DataLab } from "@/components/data";
import { cn } from "@/lib/utils";

function NarrativeModule() {
  return (
    <div className="space-y-6">
      <div className="card p-8 text-center">
        <div className="w-16 h-16 rounded-2xl bg-module-narrative-soft mx-auto mb-4 flex items-center justify-center">
          <svg className="w-8 h-8 text-module-narrative" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-text-primary mb-2">Narrative Intelligence</h3>
        <p className="text-text-secondary max-w-md mx-auto">
          Structure analysis and argument mapping. Ensure your thesis has a coherent narrative thread throughout.
        </p>
      </div>
    </div>
  );
}

function LibraryModule() {
  return (
    <div className="space-y-6">
      <div className="card p-8 text-center">
        <div className="w-16 h-16 rounded-2xl bg-module-library-soft mx-auto mb-4 flex items-center justify-center">
          <svg className="w-8 h-8 text-module-library" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-text-primary mb-2">Library</h3>
        <p className="text-text-secondary max-w-md mx-auto">
          Zotero integration for citations and bibliography management. Get smart citation suggestions as you write.
        </p>
      </div>
    </div>
  );
}

function AuditorModule() {
  return (
    <div className="space-y-6">
      <div className="card p-8 text-center">
        <div className="w-16 h-16 rounded-2xl bg-module-auditor-soft mx-auto mb-4 flex items-center justify-center">
          <svg className="w-8 h-8 text-module-auditor" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-text-primary mb-2">Brookes Auditor</h3>
        <p className="text-text-secondary max-w-md mx-auto">
          Evaluate your thesis against Oxford Brookes criteria. Get detailed feedback on formatting, structure, and compliance.
        </p>
      </div>
    </div>
  );
}

export default function Home() {
  const { activeModule, sidebarCollapsed } = useAppStore();

  const renderModule = () => {
    switch (activeModule) {
      case "writing":
        return <WritingDesk />;
      case "data":
        return <DataLab />;
      case "narrative":
        return <NarrativeModule />;
      case "library":
        return <LibraryModule />;
      case "auditor":
        return <AuditorModule />;
      default:
        return <WritingDesk />;
    }
  };

  return (
    <div className="min-h-screen bg-bg-secondary">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <main
        className={cn(
          "min-h-screen transition-all duration-200",
          sidebarCollapsed ? "ml-sidebar-collapsed" : "ml-sidebar"
        )}
      >
        {/* Header */}
        <Header />

        {/* Module Content */}
        <div className={cn(
          activeModule === "writing" ? "" : "p-6"
        )}>
          {renderModule()}
        </div>
      </main>
    </div>
  );
}
