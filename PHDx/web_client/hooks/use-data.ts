import { useMutation, useQuery } from "@tanstack/react-query";
import { useDataStore } from "@/stores/data-store";
import { safeUpload, safePost, safeFetch } from "@/lib/api";
import {
  DatasetSchema,
  PreviewResponseSchema,
  EDAResultSchema,
  SentimentResultSchema,
  VisualizationResponseSchema,
  type Dataset,
  type EDAResult,
  type SentimentResult,
} from "@/lib/schemas";

// Upload file mutation
export function useUploadFile() {
  const { addDataset, setIsUploading, setUploadProgress, setSelectedDatasetId, setActiveView } =
    useDataStore();

  return useMutation({
    mutationFn: async (file: File): Promise<Dataset> => {
      setIsUploading(true);
      setUploadProgress(0);

      const formData = new FormData();
      formData.append("file", file);

      setUploadProgress(50);
      const data = await safeUpload("/api/data/upload", DatasetSchema, formData);
      setUploadProgress(100);
      return data;
    },
    onSuccess: (data) => {
      addDataset(data);
      setSelectedDatasetId(data.id);
      setActiveView("preview");
      setIsUploading(false);
    },
    onError: () => {
      setIsUploading(false);
      setUploadProgress(0);
    },
  });
}

// Get dataset preview
export function useDatasetPreview(datasetId: string | null) {
  const { setPreviewData } = useDataStore();

  return useQuery({
    queryKey: ["dataset-preview", datasetId],
    queryFn: async () => {
      if (!datasetId) return null;

      const data = await safeFetch(
        `/api/data/preview/${datasetId}`,
        PreviewResponseSchema
      );
      setPreviewData(data.rows);
      return data;
    },
    enabled: !!datasetId,
  });
}

// Run EDA mutation
export function useRunEDA() {
  const { setEdaResult, setIsRunningEda, setActiveView } = useDataStore();

  return useMutation({
    mutationFn: async (datasetId: string): Promise<EDAResult> => {
      setIsRunningEda(true);
      return safePost(`/api/data/eda/${datasetId}`, EDAResultSchema);
    },
    onSuccess: (data) => {
      setEdaResult(data);
      setActiveView("eda");
      setIsRunningEda(false);
    },
    onError: () => {
      setIsRunningEda(false);
    },
  });
}

// Run sentiment analysis mutation
export function useAnalyzeSentiment() {
  const { setSentimentResult, setIsAnalyzingSentiment, setActiveView } = useDataStore();

  return useMutation({
    mutationFn: async ({
      datasetId,
      textColumn,
    }: {
      datasetId: string;
      textColumn: string;
    }): Promise<SentimentResult> => {
      setIsAnalyzingSentiment(true);
      return safePost(`/api/data/sentiment/${datasetId}`, SentimentResultSchema, {
        text_column: textColumn,
      });
    },
    onSuccess: (data) => {
      setSentimentResult(data);
      setActiveView("sentiment");
      setIsAnalyzingSentiment(false);
    },
    onError: () => {
      setIsAnalyzingSentiment(false);
    },
  });
}

// Generate visualization mutation
export function useGenerateVisualization() {
  return useMutation({
    mutationFn: async ({
      datasetId,
      chartType,
      xColumn,
      yColumn,
    }: {
      datasetId: string;
      chartType: string;
      xColumn: string;
      yColumn?: string;
    }) => {
      return safePost(`/api/data/visualize/${datasetId}`, VisualizationResponseSchema, {
        chart_type: chartType,
        x_column: xColumn,
        y_column: yColumn,
      });
    },
  });
}
