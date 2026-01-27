import { create } from "zustand";

export interface ChapterSection {
  id: string;
  title: string;
  content?: string;
  children?: ChapterSection[];
  status: "draft" | "in_progress" | "complete";
}

export interface Outline {
  thesis_title: string;
  chapters: ChapterSection[];
}

export interface GapItem {
  id: string;
  type: "evidence" | "citation" | "transition" | "clarity";
  description: string;
  location: string;
  suggestion?: string;
  severity: "low" | "medium" | "high";
}

interface WritingState {
  // Outline state
  outline: Outline | null;
  setOutline: (outline: Outline) => void;
  isGeneratingOutline: boolean;
  setIsGeneratingOutline: (loading: boolean) => void;

  // Selected section
  selectedSectionId: string | null;
  setSelectedSectionId: (id: string | null) => void;

  // Draft content
  draftContent: string;
  setDraftContent: (content: string) => void;
  isGeneratingDraft: boolean;
  setIsGeneratingDraft: (loading: boolean) => void;

  // Gap analysis
  gaps: GapItem[];
  setGaps: (gaps: GapItem[]) => void;
  isAnalyzingGaps: boolean;
  setIsAnalyzingGaps: (loading: boolean) => void;
  showGapPanel: boolean;
  toggleGapPanel: () => void;

  // Streaming state
  streamingText: string;
  appendStreamingText: (text: string) => void;
  clearStreamingText: () => void;
}

export const useWritingStore = create<WritingState>((set) => ({
  // Outline
  outline: null,
  setOutline: (outline) => set({ outline }),
  isGeneratingOutline: false,
  setIsGeneratingOutline: (loading) => set({ isGeneratingOutline: loading }),

  // Selected section
  selectedSectionId: null,
  setSelectedSectionId: (id) => set({ selectedSectionId: id }),

  // Draft content
  draftContent: "",
  setDraftContent: (content) => set({ draftContent: content }),
  isGeneratingDraft: false,
  setIsGeneratingDraft: (loading) => set({ isGeneratingDraft: loading }),

  // Gap analysis
  gaps: [],
  setGaps: (gaps) => set({ gaps }),
  isAnalyzingGaps: false,
  setIsAnalyzingGaps: (loading) => set({ isAnalyzingGaps: loading }),
  showGapPanel: false,
  toggleGapPanel: () => set((state) => ({ showGapPanel: !state.showGapPanel })),

  // Streaming
  streamingText: "",
  appendStreamingText: (text) =>
    set((state) => ({ streamingText: state.streamingText + text })),
  clearStreamingText: () => set({ streamingText: "" }),
}));
