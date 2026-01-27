import { useMutation } from "@tanstack/react-query";
import { useWritingStore } from "@/stores/writing-store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types for API requests
interface GenerateOutlineRequest {
  thesis_title: string;
  research_questions: string[];
  chapter_count?: number;
}

interface GenerateDraftRequest {
  section_title: string;
  outline_context: string;
  existing_content?: string;
  word_count_target?: number;
  use_dna_voice?: boolean;
}

interface GapAnalysisRequest {
  content: string;
  section_type: string;
}

interface CitationSuggestionRequest {
  content: string;
  max_suggestions?: number;
}

// Generate outline mutation
export function useGenerateOutline() {
  const { setOutline, setIsGeneratingOutline } = useWritingStore();

  return useMutation({
    mutationFn: async (data: GenerateOutlineRequest) => {
      setIsGeneratingOutline(true);
      const response = await fetch(`${API_BASE}/api/writing/outline/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error("Failed to generate outline");
      return response.json();
    },
    onSuccess: (data) => {
      setOutline(data.outline);
      setIsGeneratingOutline(false);
    },
    onError: () => {
      setIsGeneratingOutline(false);
    },
  });
}

// Generate draft mutation
export function useGenerateDraft() {
  const { setDraftContent, setIsGeneratingDraft } = useWritingStore();

  return useMutation({
    mutationFn: async (data: GenerateDraftRequest) => {
      setIsGeneratingDraft(true);
      const response = await fetch(`${API_BASE}/api/writing/draft/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error("Failed to generate draft");
      return response.json();
    },
    onSuccess: (data) => {
      setDraftContent(data.draft);
      setIsGeneratingDraft(false);
    },
    onError: () => {
      setIsGeneratingDraft(false);
    },
  });
}

// Streaming draft generation
export function useStreamDraft() {
  const {
    appendStreamingText,
    clearStreamingText,
    setIsGeneratingDraft,
    setDraftContent
  } = useWritingStore();

  const streamDraft = async (data: GenerateDraftRequest) => {
    clearStreamingText();
    setIsGeneratingDraft(true);

    try {
      const response = await fetch(`${API_BASE}/api/writing/draft/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!response.ok) throw new Error("Failed to start stream");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      if (!reader) throw new Error("No response body");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") continue;

            try {
              const parsed = JSON.parse(data);
              if (parsed.text) {
                appendStreamingText(parsed.text);
                fullText += parsed.text;
              }
            } catch {
              // Ignore parse errors for partial chunks
            }
          }
        }
      }

      setDraftContent(fullText);
    } finally {
      setIsGeneratingDraft(false);
    }
  };

  return { streamDraft };
}

// Gap analysis mutation
export function useAnalyzeGaps() {
  const { setGaps, setIsAnalyzingGaps } = useWritingStore();

  return useMutation({
    mutationFn: async (data: GapAnalysisRequest) => {
      setIsAnalyzingGaps(true);
      const response = await fetch(`${API_BASE}/api/writing/draft/analyze-gaps`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error("Failed to analyze gaps");
      return response.json();
    },
    onSuccess: (data) => {
      setGaps(data.gaps || []);
      setIsAnalyzingGaps(false);
    },
    onError: () => {
      setIsAnalyzingGaps(false);
    },
  });
}

// Citation suggestions mutation
export function useSuggestCitations() {
  return useMutation({
    mutationFn: async (data: CitationSuggestionRequest) => {
      const response = await fetch(`${API_BASE}/api/writing/citations/suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error("Failed to suggest citations");
      return response.json();
    },
  });
}
