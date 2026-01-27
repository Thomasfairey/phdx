"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useWritingStore, ChapterSection } from "@/stores/writing-store";
import { ChevronRight, ChevronDown, FileText, Circle, CheckCircle2, Clock } from "lucide-react";

interface OutlineItemProps {
  section: ChapterSection;
  depth?: number;
}

function OutlineItem({ section, depth = 0 }: OutlineItemProps) {
  const [expanded, setExpanded] = useState(true);
  const { selectedSectionId, setSelectedSectionId } = useWritingStore();

  const hasChildren = section.children && section.children.length > 0;
  const isSelected = selectedSectionId === section.id;

  const statusIcon = {
    draft: <Circle className="w-3.5 h-3.5 text-text-tertiary" />,
    in_progress: <Clock className="w-3.5 h-3.5 text-warning" />,
    complete: <CheckCircle2 className="w-3.5 h-3.5 text-success" />,
  };

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors",
          "hover:bg-bg-hover",
          isSelected && "bg-module-writing-soft text-module-writing"
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => setSelectedSectionId(section.id)}
      >
        {/* Expand/Collapse Toggle */}
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
            className="p-0.5 hover:bg-bg-active rounded"
          >
            {expanded ? (
              <ChevronDown className="w-4 h-4 text-text-tertiary" />
            ) : (
              <ChevronRight className="w-4 h-4 text-text-tertiary" />
            )}
          </button>
        ) : (
          <span className="w-5" />
        )}

        {/* Icon */}
        <FileText className={cn(
          "w-4 h-4 flex-shrink-0",
          isSelected ? "text-module-writing" : "text-text-secondary"
        )} />

        {/* Title */}
        <span className={cn(
          "flex-1 text-sm truncate",
          isSelected ? "font-medium" : "text-text-primary"
        )}>
          {section.title}
        </span>

        {/* Status */}
        {statusIcon[section.status]}
      </div>

      {/* Children */}
      {hasChildren && expanded && (
        <div className="animate-fade-in">
          {section.children!.map((child) => (
            <OutlineItem key={child.id} section={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function ChapterOutline() {
  const { outline } = useWritingStore();

  if (!outline) {
    return null;
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border">
        <h3 className="font-semibold text-text-primary truncate">
          {outline.thesis_title}
        </h3>
        <p className="text-xs text-text-tertiary mt-0.5">
          {outline.chapters.length} chapters
        </p>
      </div>

      {/* Outline Tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {outline.chapters.map((chapter) => (
          <OutlineItem key={chapter.id} section={chapter} />
        ))}
      </div>
    </div>
  );
}
