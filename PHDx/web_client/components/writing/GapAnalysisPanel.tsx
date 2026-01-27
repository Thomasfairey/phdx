"use client";

import { useWritingStore, GapItem } from "@/stores/writing-store";
import { useAnalyzeGaps } from "@/hooks/use-writing";
import { Button, Card, Badge, Spinner, EmptyState } from "@/components/ui";
import { cn } from "@/lib/utils";
import {
  X,
  AlertCircle,
  BookOpen,
  ArrowRight,
  Lightbulb,
  RefreshCw,
} from "lucide-react";

const gapTypeConfig: Record<GapItem["type"], { icon: typeof AlertCircle; label: string; color: string }> = {
  evidence: {
    icon: AlertCircle,
    label: "Missing Evidence",
    color: "error",
  },
  citation: {
    icon: BookOpen,
    label: "Citation Needed",
    color: "warning",
  },
  transition: {
    icon: ArrowRight,
    label: "Weak Transition",
    color: "info",
  },
  clarity: {
    icon: Lightbulb,
    label: "Clarity Issue",
    color: "warning",
  },
};

function GapCard({ gap }: { gap: GapItem }) {
  const config = gapTypeConfig[gap.type];
  const Icon = config.icon;

  return (
    <Card className="p-3">
      <div className="flex items-start gap-3">
        <div className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
          gap.type === "evidence" && "bg-error-soft",
          gap.type === "citation" && "bg-warning-soft",
          gap.type === "transition" && "bg-info-soft",
          gap.type === "clarity" && "bg-warning-soft"
        )}>
          <Icon className={cn(
            "w-4 h-4",
            gap.type === "evidence" && "text-error",
            gap.type === "citation" && "text-warning",
            gap.type === "transition" && "text-info",
            gap.type === "clarity" && "text-warning"
          )} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-text-primary">
              {config.label}
            </span>
            <Badge
              variant={gap.severity === "high" ? "error" : gap.severity === "medium" ? "warning" : "neutral"}
            >
              {gap.severity}
            </Badge>
          </div>

          <p className="text-sm text-text-secondary mb-2">
            {gap.description}
          </p>

          {gap.suggestion && (
            <div className="text-xs text-text-tertiary bg-bg-tertiary rounded-md p-2">
              <span className="font-medium">Suggestion: </span>
              {gap.suggestion}
            </div>
          )}

          <p className="text-xs text-text-tertiary mt-2">
            Location: {gap.location}
          </p>
        </div>
      </div>
    </Card>
  );
}

export function GapAnalysisPanel() {
  const {
    gaps,
    isAnalyzingGaps,
    showGapPanel,
    toggleGapPanel,
    draftContent,
    selectedSectionId,
  } = useWritingStore();

  const analyzeGaps = useAnalyzeGaps();

  const handleAnalyze = () => {
    if (!draftContent.trim()) return;

    analyzeGaps.mutate({
      content: draftContent,
      section_type: "chapter", // Could be dynamic based on selected section
    });
  };

  if (!showGapPanel) return null;

  return (
    <aside className="w-80 border-l border-border bg-bg-primary h-full flex flex-col animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h3 className="font-semibold text-text-primary">Gap Analysis</h3>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleGapPanel}
        >
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isAnalyzingGaps ? (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <Spinner size="lg" />
            <p className="text-sm text-text-secondary">Analyzing gaps...</p>
          </div>
        ) : gaps.length === 0 ? (
          <EmptyState
            title="No gaps analyzed"
            description="Click the analyze button to check your content for gaps and suggestions"
            icon={<AlertCircle className="w-8 h-8" />}
          />
        ) : (
          <div className="space-y-3">
            {/* Summary */}
            <div className="flex items-center gap-2 text-sm text-text-secondary mb-4">
              <span className="font-medium">{gaps.length}</span>
              <span>items found</span>
            </div>

            {/* Gap Cards */}
            {gaps.map((gap) => (
              <GapCard key={gap.id} gap={gap} />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <Button
          onClick={handleAnalyze}
          loading={isAnalyzingGaps}
          disabled={!draftContent.trim()}
          className="w-full"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Analyze Content
        </Button>
      </div>
    </aside>
  );
}
