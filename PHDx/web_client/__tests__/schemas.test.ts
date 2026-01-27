import { describe, it, expect } from "vitest";
import {
  DatasetSchema,
  PreviewResponseSchema,
  EDAResultSchema,
  SentimentResultSchema,
} from "@/lib/schemas";

describe("DatasetSchema", () => {
  it("should validate a valid dataset", () => {
    const validDataset = {
      id: "abc123",
      filename: "test.csv",
      rows: 100,
      columns: 5,
      columns_list: ["a", "b", "c", "d", "e"],
      uploaded_at: "2024-01-01T00:00:00Z",
    };

    const result = DatasetSchema.safeParse(validDataset);
    expect(result.success).toBe(true);
  });

  it("should reject dataset with missing fields", () => {
    const invalidDataset = {
      id: "abc123",
      filename: "test.csv",
      // missing rows, columns, columns_list, uploaded_at
    };

    const result = DatasetSchema.safeParse(invalidDataset);
    expect(result.success).toBe(false);
  });

  it("should reject dataset with wrong types", () => {
    const invalidDataset = {
      id: "abc123",
      filename: "test.csv",
      rows: "100", // should be number
      columns: 5,
      columns_list: ["a", "b"],
      uploaded_at: "2024-01-01",
    };

    const result = DatasetSchema.safeParse(invalidDataset);
    expect(result.success).toBe(false);
  });
});

describe("PreviewResponseSchema", () => {
  it("should validate preview response with rows", () => {
    const validPreview = {
      rows: [
        { id: 1, name: "test" },
        { id: 2, name: "test2" },
      ],
    };

    const result = PreviewResponseSchema.safeParse(validPreview);
    expect(result.success).toBe(true);
  });

  it("should validate preview response with total_rows", () => {
    const validPreview = {
      rows: [],
      total_rows: 0,
    };

    const result = PreviewResponseSchema.safeParse(validPreview);
    expect(result.success).toBe(true);
  });
});

describe("EDAResultSchema", () => {
  it("should validate a valid EDA result", () => {
    const validEDA = {
      summary: {
        total_rows: 100,
        total_columns: 5,
        memory_usage: "1.5 KB",
      },
      column_types: { col1: "int64", col2: "object" },
      missing_values: { col1: 0, col2: 5 },
      numeric_stats: { col1: { mean: 50, std: 10 } },
      categorical_stats: { col2: { unique: 3, top: "value", frequency: 40 } },
    };

    const result = EDAResultSchema.safeParse(validEDA);
    expect(result.success).toBe(true);
  });
});

describe("SentimentResultSchema", () => {
  it("should validate a valid sentiment result", () => {
    const validSentiment = {
      overall: {
        positive: 0.6,
        negative: 0.2,
        neutral: 0.2,
      },
      by_row: [
        { text: "Great!", sentiment: "positive", confidence: 0.95 },
        { text: "Bad.", sentiment: "negative", confidence: 0.88 },
      ],
    };

    const result = SentimentResultSchema.safeParse(validSentiment);
    expect(result.success).toBe(true);
  });

  it("should reject invalid sentiment values", () => {
    const invalidSentiment = {
      overall: {
        positive: 0.6,
        negative: 0.2,
        neutral: 0.2,
      },
      by_row: [
        { text: "Test", sentiment: "unknown", confidence: 0.5 }, // invalid sentiment
      ],
    };

    const result = SentimentResultSchema.safeParse(invalidSentiment);
    expect(result.success).toBe(false);
  });
});
