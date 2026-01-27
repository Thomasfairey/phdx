import { z } from "zod";

// Dataset schema - matches backend Pydantic model
export const DatasetSchema = z.object({
  id: z.string(),
  filename: z.string(),
  rows: z.number(),
  columns: z.number(),
  columns_list: z.array(z.string()),
  uploaded_at: z.string(),
});

export type Dataset = z.infer<typeof DatasetSchema>;

// Preview response schema
export const PreviewResponseSchema = z.object({
  rows: z.array(z.record(z.unknown())),
  total_rows: z.number().optional(),
});

export type PreviewResponse = z.infer<typeof PreviewResponseSchema>;

// EDA Result schema
export const EDAResultSchema = z.object({
  summary: z.object({
    total_rows: z.number(),
    total_columns: z.number(),
    memory_usage: z.string(),
  }),
  column_types: z.record(z.string()),
  missing_values: z.record(z.number()),
  numeric_stats: z.record(z.record(z.number())),
  categorical_stats: z.record(
    z.object({
      unique: z.number(),
      top: z.string(),
      frequency: z.number(),
    })
  ),
});

export type EDAResult = z.infer<typeof EDAResultSchema>;

// Sentiment Result schema
export const SentimentResultSchema = z.object({
  overall: z.object({
    positive: z.number(),
    negative: z.number(),
    neutral: z.number(),
  }),
  by_row: z.array(
    z.object({
      text: z.string(),
      sentiment: z.enum(["positive", "negative", "neutral"]),
      confidence: z.number(),
    })
  ),
});

export type SentimentResult = z.infer<typeof SentimentResultSchema>;

// Visualization response schema
export const VisualizationResponseSchema = z.object({
  chart_type: z.string(),
  data: z.array(z.record(z.unknown())),
  x_column: z.string(),
  y_column: z.string().optional(),
});

export type VisualizationResponse = z.infer<typeof VisualizationResponseSchema>;

// Health check response
export const HealthResponseSchema = z.object({
  status: z.string(),
  version: z.string().optional(),
  timestamp: z.string().optional(),
});

export type HealthResponse = z.infer<typeof HealthResponseSchema>;

// API Error response
export const APIErrorSchema = z.object({
  detail: z.string(),
});
