"use client";

import { useDataStore } from "@/stores/data-store";
import { useDatasetPreview } from "@/hooks/use-data";
import { Card, Skeleton, EmptyState } from "@/components/ui";
import { cn } from "@/lib/utils";
import { Table } from "lucide-react";

export function DataPreview() {
  const { selectedDatasetId, datasets, previewData } = useDataStore();
  const { isLoading, isError } = useDatasetPreview(selectedDatasetId);

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);

  if (!selectedDatasetId || !selectedDataset) {
    return (
      <EmptyState
        title="No dataset selected"
        description="Upload a file or select a dataset to preview"
        icon={<Table className="w-8 h-8" />}
      />
    );
  }

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-[400px] w-full" />
        </div>
      </Card>
    );
  }

  if (isError) {
    return (
      <EmptyState
        title="Failed to load preview"
        description="There was an error loading the data preview"
        icon={<Table className="w-8 h-8" />}
      />
    );
  }

  const columns = selectedDataset.columns_list || [];
  const rows = previewData || [];

  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border bg-bg-secondary">
        <h3 className="font-semibold text-text-primary">{selectedDataset.filename}</h3>
        <p className="text-xs text-text-tertiary mt-0.5">
          {selectedDataset.rows.toLocaleString()} rows × {selectedDataset.columns} columns
        </p>
      </div>

      {/* Table */}
      <div className="overflow-auto max-h-[500px]">
        <table className="w-full text-sm">
          <thead className="bg-bg-tertiary sticky top-0">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-text-secondary border-b border-border w-12">
                #
              </th>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2 text-left text-xs font-medium text-text-secondary border-b border-border whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={i}
                className={cn(
                  "hover:bg-bg-hover transition-colors",
                  i % 2 === 0 ? "bg-bg-primary" : "bg-bg-secondary/50"
                )}
              >
                <td className="px-4 py-2 text-text-tertiary text-xs border-b border-border">
                  {i + 1}
                </td>
                {columns.map((col) => (
                  <td
                    key={col}
                    className="px-4 py-2 text-text-primary border-b border-border whitespace-nowrap max-w-[200px] truncate"
                  >
                    {String(row[col] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-border bg-bg-secondary text-xs text-text-tertiary">
        Showing first {rows.length} rows
      </div>
    </Card>
  );
}
