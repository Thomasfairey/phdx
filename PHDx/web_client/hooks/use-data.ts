import { useMutation, useQuery } from "@tanstack/react-query";
import { useDataStore, Dataset, EDAResult, SentimentResult } from "@/stores/data-store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

      const response = await fetch(`${API_BASE}/api/data/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to upload file");
      }

      setUploadProgress(100);
      return response.json();
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

      const response = await fetch(`${API_BASE}/api/data/preview/${datasetId}`);
      if (!response.ok) throw new Error("Failed to get preview");

      const data = await response.json();
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

      const response = await fetch(`${API_BASE}/api/data/eda/${datasetId}`, {
        method: "POST",
      });

      if (!response.ok) throw new Error("Failed to run EDA");
      return response.json();
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

      const response = await fetch(`${API_BASE}/api/data/sentiment/${datasetId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text_column: textColumn }),
      });

      if (!response.ok) throw new Error("Failed to analyze sentiment");
      return response.json();
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
      const response = await fetch(`${API_BASE}/api/data/visualize/${datasetId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chart_type: chartType,
          x_column: xColumn,
          y_column: yColumn,
        }),
      });

      if (!response.ok) throw new Error("Failed to generate visualization");
      return response.json();
    },
  });
}
