import { create } from "zustand";

export interface Dataset {
  id: string;
  filename: string;
  rows: number;
  columns: number;
  columns_list: string[];
  uploaded_at: string;
}

export interface EDAResult {
  summary: {
    total_rows: number;
    total_columns: number;
    memory_usage: string;
  };
  column_types: Record<string, string>;
  missing_values: Record<string, number>;
  numeric_stats: Record<string, Record<string, number>>;
  categorical_stats: Record<string, { unique: number; top: string; frequency: number }>;
}

export interface SentimentResult {
  overall: {
    positive: number;
    negative: number;
    neutral: number;
  };
  by_row: Array<{
    text: string;
    sentiment: "positive" | "negative" | "neutral";
    confidence: number;
  }>;
}

interface DataState {
  // Datasets
  datasets: Dataset[];
  setDatasets: (datasets: Dataset[]) => void;
  addDataset: (dataset: Dataset) => void;
  selectedDatasetId: string | null;
  setSelectedDatasetId: (id: string | null) => void;

  // Upload state
  isUploading: boolean;
  setIsUploading: (loading: boolean) => void;
  uploadProgress: number;
  setUploadProgress: (progress: number) => void;

  // Preview data
  previewData: Record<string, unknown>[] | null;
  setPreviewData: (data: Record<string, unknown>[] | null) => void;

  // EDA
  edaResult: EDAResult | null;
  setEdaResult: (result: EDAResult | null) => void;
  isRunningEda: boolean;
  setIsRunningEda: (loading: boolean) => void;

  // Sentiment
  sentimentResult: SentimentResult | null;
  setSentimentResult: (result: SentimentResult | null) => void;
  isAnalyzingSentiment: boolean;
  setIsAnalyzingSentiment: (loading: boolean) => void;

  // Active view
  activeView: "upload" | "preview" | "eda" | "sentiment" | "visualize";
  setActiveView: (view: DataState["activeView"]) => void;
}

export const useDataStore = create<DataState>((set) => ({
  // Datasets
  datasets: [],
  setDatasets: (datasets) => set({ datasets }),
  addDataset: (dataset) =>
    set((state) => ({ datasets: [...state.datasets, dataset] })),
  selectedDatasetId: null,
  setSelectedDatasetId: (id) => set({ selectedDatasetId: id }),

  // Upload
  isUploading: false,
  setIsUploading: (loading) => set({ isUploading: loading }),
  uploadProgress: 0,
  setUploadProgress: (progress) => set({ uploadProgress: progress }),

  // Preview
  previewData: null,
  setPreviewData: (data) => set({ previewData: data }),

  // EDA
  edaResult: null,
  setEdaResult: (result) => set({ edaResult: result }),
  isRunningEda: false,
  setIsRunningEda: (loading) => set({ isRunningEda: loading }),

  // Sentiment
  sentimentResult: null,
  setSentimentResult: (result) => set({ sentimentResult: result }),
  isAnalyzingSentiment: false,
  setIsAnalyzingSentiment: (loading) => set({ isAnalyzingSentiment: loading }),

  // View
  activeView: "upload",
  setActiveView: (view) => set({ activeView: view }),
}));
