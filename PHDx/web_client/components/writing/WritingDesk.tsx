"use client";

import { useWritingStore } from "@/stores/writing-store";
import { OutlineGenerator } from "./OutlineGenerator";
import { ChapterOutline } from "./ChapterOutline";
import { DraftEditor } from "./DraftEditor";
import { GapAnalysisPanel } from "./GapAnalysisPanel";
import { cn } from "@/lib/utils";

export function WritingDesk() {
  const { outline, showGapPanel } = useWritingStore();

  // Show outline generator if no outline exists
  if (!outline) {
    return (
      <div className="h-[calc(100vh-var(--header-height)-48px)] flex items-center justify-center p-6">
        <OutlineGenerator />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-var(--header-height)-48px)] flex">
      {/* Left: Chapter Outline */}
      <aside className="w-64 border-r border-border bg-bg-primary flex-shrink-0">
        <ChapterOutline />
      </aside>

      {/* Center: Draft Editor */}
      <main className="flex-1 bg-bg-secondary min-w-0">
        <DraftEditor />
      </main>

      {/* Right: Gap Analysis Panel (Conditional) */}
      {showGapPanel && <GapAnalysisPanel />}
    </div>
  );
}
