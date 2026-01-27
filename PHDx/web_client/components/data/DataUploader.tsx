"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useDataStore } from "@/stores/data-store";
import { useUploadFile } from "@/hooks/use-data";
import { Card, Progress, Spinner } from "@/components/ui";
import { cn } from "@/lib/utils";
import { Upload, FileSpreadsheet, AlertCircle } from "lucide-react";

export function DataUploader() {
  const { isUploading, uploadProgress } = useDataStore();
  const uploadFile = useUploadFile();

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        uploadFile.mutate(acceptedFiles[0]);
      }
    },
    [uploadFile]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    maxFiles: 1,
    disabled: isUploading,
  });

  return (
    <div className="max-w-2xl mx-auto">
      <Card className="p-8">
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all",
            "hover:border-accent-primary hover:bg-accent-primary-soft",
            isDragActive && "border-accent-primary bg-accent-primary-soft",
            isDragReject && "border-error bg-error-soft",
            isUploading && "opacity-50 cursor-not-allowed"
          )}
        >
          <input {...getInputProps()} />

          {isUploading ? (
            <div className="space-y-4">
              <Spinner size="lg" className="mx-auto" />
              <p className="text-text-secondary">Uploading file...</p>
              <Progress value={uploadProgress} className="max-w-xs mx-auto" />
            </div>
          ) : isDragReject ? (
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-error-soft mx-auto flex items-center justify-center">
                <AlertCircle className="w-8 h-8 text-error" />
              </div>
              <div>
                <p className="text-lg font-medium text-error">Invalid file type</p>
                <p className="text-sm text-text-secondary mt-1">
                  Please upload a CSV or Excel file
                </p>
              </div>
            </div>
          ) : isDragActive ? (
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-accent-primary-soft mx-auto flex items-center justify-center">
                <Upload className="w-8 h-8 text-accent-primary" />
              </div>
              <p className="text-lg font-medium text-accent-primary">
                Drop your file here
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-module-data-soft mx-auto flex items-center justify-center">
                <FileSpreadsheet className="w-8 h-8 text-module-data" />
              </div>
              <div>
                <p className="text-lg font-medium text-text-primary">
                  Drag & drop your data file
                </p>
                <p className="text-sm text-text-secondary mt-1">
                  or click to browse
                </p>
              </div>
              <p className="text-xs text-text-tertiary">
                Supports CSV, XLS, XLSX files
              </p>
            </div>
          )}
        </div>

        {uploadFile.isError && (
          <div className="mt-4 p-4 rounded-lg bg-error-soft border border-error/20">
            <p className="text-sm text-error flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {uploadFile.error?.message || "Failed to upload file"}
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
