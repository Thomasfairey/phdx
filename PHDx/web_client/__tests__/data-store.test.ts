import { describe, it, expect, beforeEach } from "vitest";
import { useDataStore, type Dataset } from "@/stores/data-store";

describe("useDataStore", () => {
  beforeEach(() => {
    // Reset store state before each test
    useDataStore.setState({
      datasets: [],
      selectedDatasetId: null,
      isUploading: false,
      uploadProgress: 0,
      previewData: null,
      edaResult: null,
      isRunningEda: false,
      sentimentResult: null,
      isAnalyzingSentiment: false,
      activeView: "upload",
    });
  });

  it("should initialize with empty datasets", () => {
    const { datasets } = useDataStore.getState();
    expect(datasets).toEqual([]);
  });

  it("should set datasets", () => {
    const mockDatasets: Dataset[] = [
      {
        id: "1",
        filename: "test.csv",
        rows: 100,
        columns: 5,
        columns_list: ["a", "b", "c", "d", "e"],
        uploaded_at: "2024-01-01T00:00:00Z",
      },
    ];

    useDataStore.getState().setDatasets(mockDatasets);
    expect(useDataStore.getState().datasets).toEqual(mockDatasets);
  });

  it("should add a dataset", () => {
    const dataset: Dataset = {
      id: "2",
      filename: "another.csv",
      rows: 50,
      columns: 3,
      columns_list: ["x", "y", "z"],
      uploaded_at: "2024-01-02T00:00:00Z",
    };

    useDataStore.getState().addDataset(dataset);
    expect(useDataStore.getState().datasets).toHaveLength(1);
    expect(useDataStore.getState().datasets[0]).toEqual(dataset);
  });

  it("should select a dataset by id", () => {
    useDataStore.getState().setSelectedDatasetId("test-id");
    expect(useDataStore.getState().selectedDatasetId).toBe("test-id");
  });

  it("should toggle upload state", () => {
    expect(useDataStore.getState().isUploading).toBe(false);
    useDataStore.getState().setIsUploading(true);
    expect(useDataStore.getState().isUploading).toBe(true);
  });

  it("should update upload progress", () => {
    useDataStore.getState().setUploadProgress(50);
    expect(useDataStore.getState().uploadProgress).toBe(50);
  });

  it("should change active view", () => {
    expect(useDataStore.getState().activeView).toBe("upload");
    useDataStore.getState().setActiveView("eda");
    expect(useDataStore.getState().activeView).toBe("eda");
  });
});
