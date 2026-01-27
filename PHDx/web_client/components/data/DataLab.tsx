"use client";

import { useDataStore } from "@/stores/data-store";
import { useRunEDA, useAnalyzeSentiment } from "@/hooks/use-data";
import { DataUploader } from "./DataUploader";
import { DataPreview } from "./DataPreview";
import { EDAResults } from "./EDAResults";
import { SentimentResults } from "./SentimentResults";
import { Button, Card, Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui";
import { cn } from "@/lib/utils";
import {
  Upload,
  Table,
  BarChart3,
  MessageSquare,
  LineChart,
  Play,
  FileSpreadsheet,
} from "lucide-react";

function DatasetSelector() {
  const { datasets, selectedDatasetId, setSelectedDatasetId, setActiveView } = useDataStore();

  if (datasets.length === 0) return null;

  return (
    <Card className="p-3 mb-4">
      <div className="flex items-center gap-3 overflow-x-auto">
        <span className="text-xs text-text-secondary flex-shrink-0">Datasets:</span>
        {datasets.map((dataset) => (
          <button
            key={dataset.id}
            onClick={() => {
              setSelectedDatasetId(dataset.id);
              setActiveView("preview");
            }}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors flex-shrink-0",
              "hover:bg-bg-hover",
              selectedDatasetId === dataset.id
                ? "bg-module-data-soft text-module-data"
                : "text-text-secondary"
            )}
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span className="truncate max-w-[150px]">{dataset.filename}</span>
          </button>
        ))}
      </div>
    </Card>
  );
}

function ActionBar() {
  const { selectedDatasetId, datasets, isRunningEda, isAnalyzingSentiment } = useDataStore();
  const runEDA = useRunEDA();
  const analyzeSentiment = useAnalyzeSentiment();

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);

  if (!selectedDatasetId || !selectedDataset) return null;

  // Find a text column for sentiment (simple heuristic)
  const textColumn = selectedDataset.columns_list.find(
    (col) =>
      col.toLowerCase().includes("text") ||
      col.toLowerCase().includes("comment") ||
      col.toLowerCase().includes("review") ||
      col.toLowerCase().includes("description")
  );

  return (
    <Card className="p-3 mb-4">
      <div className="flex items-center gap-2">
        <span className="text-xs text-text-secondary">Actions:</span>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => runEDA.mutate(selectedDatasetId)}
          loading={isRunningEda}
        >
          <Play className="w-4 h-4 mr-1.5" />
          Run EDA
        </Button>
        {textColumn && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() =>
              analyzeSentiment.mutate({
                datasetId: selectedDatasetId,
                textColumn,
              })
            }
            loading={isAnalyzingSentiment}
          >
            <MessageSquare className="w-4 h-4 mr-1.5" />
            Sentiment Analysis
          </Button>
        )}
      </div>
    </Card>
  );
}

export function DataLab() {
  const { activeView, setActiveView, datasets, selectedDatasetId } = useDataStore();

  const tabs = [
    { id: "upload" as const, label: "Upload", icon: Upload },
    { id: "preview" as const, label: "Preview", icon: Table },
    { id: "eda" as const, label: "EDA", icon: BarChart3 },
    { id: "sentiment" as const, label: "Sentiment", icon: MessageSquare },
    { id: "visualize" as const, label: "Visualize", icon: LineChart },
  ];

  return (
    <div className="space-y-4">
      {/* Dataset Selector */}
      <DatasetSelector />

      {/* Tabs */}
      <Tabs value={activeView} onValueChange={(v) => setActiveView(v as typeof activeView)}>
        <TabsList>
          {tabs.map((tab) => (
            <TabsTrigger
              key={tab.id}
              value={tab.id}
              disabled={
                tab.id !== "upload" && datasets.length === 0
              }
            >
              <tab.icon className="w-4 h-4 mr-1.5" />
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <div className="mt-6">
          {/* Action Bar */}
          {activeView !== "upload" && <ActionBar />}

          <TabsContent value="upload">
            <DataUploader />
          </TabsContent>

          <TabsContent value="preview">
            <DataPreview />
          </TabsContent>

          <TabsContent value="eda">
            <EDAResults />
          </TabsContent>

          <TabsContent value="sentiment">
            <SentimentResults />
          </TabsContent>

          <TabsContent value="visualize">
            <Card className="p-8 text-center">
              <div className="w-16 h-16 rounded-2xl bg-bg-tertiary mx-auto mb-4 flex items-center justify-center">
                <LineChart className="w-8 h-8 text-text-tertiary" />
              </div>
              <h3 className="text-lg font-medium text-text-primary mb-2">
                Visualization Builder
              </h3>
              <p className="text-sm text-text-secondary max-w-md mx-auto">
                Create custom charts and visualizations from your data. Coming soon.
              </p>
            </Card>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
