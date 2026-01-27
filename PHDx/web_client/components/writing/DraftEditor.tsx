"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { useWritingStore, ChapterSection } from "@/stores/writing-store";
import { useStreamDraft } from "@/hooks/use-writing";
import { Button, Textarea, Card, Spinner } from "@/components/ui";
import { Sparkles, Search, BookOpen } from "lucide-react";

export function DraftEditor() {
  const {
    selectedSectionId,
    outline,
    draftContent,
    setDraftContent,
    streamingText,
    isGeneratingDraft,
    toggleGapPanel,
    showGapPanel,
  } = useWritingStore();

  const { streamDraft } = useStreamDraft();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Find selected section
  const findSection = (id: string, sections: ChapterSection[] | undefined): ChapterSection | null => {
    if (!sections) return null;
    for (const section of sections) {
      if (section.id === id) return section;
      if (section.children) {
        const found = findSection(id, section.children);
        if (found) return found;
      }
    }
    return null;
  };

  const selectedSection = selectedSectionId && outline
    ? findSection(selectedSectionId, outline.chapters)
    : null;

  // Auto-scroll when streaming
  useEffect(() => {
    if (streamingText && textareaRef.current) {
      textareaRef.current.scrollTop = textareaRef.current.scrollHeight;
    }
  }, [streamingText]);

  const displayContent = isGeneratingDraft ? streamingText : draftContent;

  const handleGenerateDraft = () => {
    if (!selectedSection || !outline) return;

    streamDraft({
      section_title: selectedSection.title,
      outline_context: outline.thesis_title,
      existing_content: draftContent || undefined,
      word_count_target: 500,
      use_dna_voice: true,
    });
  };

  if (!selectedSection) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center max-w-sm">
          <div className="w-16 h-16 rounded-2xl bg-bg-tertiary mx-auto mb-4 flex items-center justify-center">
            <BookOpen className="w-8 h-8 text-text-tertiary" />
          </div>
          <h3 className="text-lg font-medium text-text-primary mb-2">
            Select a section
          </h3>
          <p className="text-sm text-text-secondary">
            Choose a chapter or section from the outline to start writing or editing
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div>
          <h3 className="font-semibold text-text-primary">
            {selectedSection.title}
          </h3>
          <p className="text-xs text-text-tertiary">
            {draftContent.split(/\s+/).filter(Boolean).length} words
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleGapPanel}
            className={cn(showGapPanel && "bg-bg-active")}
          >
            <Search className="w-4 h-4 mr-1.5" />
            Gap Analysis
          </Button>
          <Button
            size="sm"
            onClick={handleGenerateDraft}
            loading={isGeneratingDraft}
          >
            <Sparkles className="w-4 h-4 mr-1.5" />
            Generate
          </Button>
        </div>
      </div>

      {/* Editor Area */}
      <div className="flex-1 p-4 overflow-hidden">
        <div className="h-full relative">
          <Textarea
            ref={textareaRef}
            value={displayContent}
            onChange={(e) => setDraftContent(e.target.value)}
            placeholder="Start writing your section here, or click Generate to create AI-assisted content..."
            className={cn(
              "h-full resize-none font-serif text-base leading-relaxed",
              isGeneratingDraft && "opacity-90"
            )}
            disabled={isGeneratingDraft}
          />

          {/* Streaming Indicator */}
          {isGeneratingDraft && (
            <div className="absolute bottom-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-bg-primary border border-border rounded-full shadow-sm">
              <Spinner size="sm" />
              <span className="text-xs text-text-secondary">Writing...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
