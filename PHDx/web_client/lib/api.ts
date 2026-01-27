/**
 * PHDx API Client Library
 *
 * Type definitions and API client for the PHDx FastAPI backend.
 * Includes Zod runtime validation for API responses.
 */

import { z } from "zod";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// Zod Validation Utilities
// =============================================================================

export class APIValidationError extends Error {
  constructor(
    message: string,
    public issues: z.ZodIssue[]
  ) {
    super(message);
    this.name = "APIValidationError";
  }
}

export class APIError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = "APIError";
  }
}

/**
 * Type-safe API fetch wrapper with Zod validation
 */
export async function safeFetch<T>(
  endpoint: string,
  schema: z.ZodSchema<T>,
  options?: RequestInit
): Promise<T> {
  const url = endpoint.startsWith("http") ? endpoint : `${API_URL}${endpoint}`;

  const response = await fetch(url, options);

  if (!response.ok) {
    let errorMessage = `API error: ${response.status}`;
    try {
      const errorBody = await response.json();
      if (errorBody.detail) {
        errorMessage = errorBody.detail;
      }
    } catch {
      // Ignore JSON parse errors
    }
    throw new APIError(errorMessage, response.status);
  }

  const data = await response.json();

  const result = schema.safeParse(data);
  if (!result.success) {
    console.error("API response validation failed:", result.error.issues);
    throw new APIValidationError(
      `API response validation failed: ${result.error.issues.map((i) => i.message).join(", ")}`,
      result.error.issues
    );
  }

  return result.data;
}

/**
 * Convenience wrapper for POST with JSON body and Zod validation
 */
export async function safePost<T>(
  endpoint: string,
  schema: z.ZodSchema<T>,
  body?: unknown
): Promise<T> {
  return safeFetch(endpoint, schema, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * Wrapper for file uploads (FormData) with Zod validation
 */
export async function safeUpload<T>(
  endpoint: string,
  schema: z.ZodSchema<T>,
  formData: FormData
): Promise<T> {
  return safeFetch(endpoint, schema, {
    method: "POST",
    body: formData,
  });
}

// =============================================================================
// API Response Types
// =============================================================================

export interface HealthResponse {
  status: string;
  timestamp: string;
}

export interface StatusResponse {
  system: string;
  environment: string;
  models: string[];
  version: string;
}

export interface SanitizeResponse {
  sanitized_text: string;
  pii_found: boolean;
  redactions_count: number;
}

export interface AuditResponse {
  audit_id: string;
  timestamp: string;
  status: string;
  context: string;
  word_count: number;
  overall_grade: {
    score: number;
    level: string;
    descriptor: string;
  };
  criteria_scores: {
    originality: { score: number; level: string; feedback: string };
    criticality: { score: number; level: string; feedback: string };
    rigour: { score: number; level: string; feedback: string };
  };
  strengths: string[];
  areas_for_improvement: string[];
  specific_recommendations: string[];
  examiner_summary: string;
  error?: string;
}

export interface DNAProfile {
  success: boolean;
  profile?: {
    total_words_analyzed: number;
    avg_sentence_length: number;
    avg_word_length: number;
    vocabulary_richness: number;
    hedging_frequency: number;
    formality_score: number;
  };
  error?: string;
}

export interface RedThreadCheckResponse {
  overall_score: number;
  status: string;
  consistency_analysis: string;
  cross_references: {
    term: string;
    occurrences: number;
    contexts: string[];
  }[];
  suggestions: string[];
}

export interface RedThreadStats {
  total_chunks: number;
  chapters_indexed: string[];
  last_indexed: string;
}

// =============================================================================
// API Client
// =============================================================================

export class PHDxAPIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Health & Status
  async health(): Promise<HealthResponse> {
    return this.fetch('/health');
  }

  async status(): Promise<StatusResponse> {
    return this.fetch('/status');
  }

  // Airlock (Sanitization)
  async sanitize(text: string): Promise<SanitizeResponse> {
    return this.fetch('/airlock/sanitize', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  }

  // Auditor
  async evaluate(text: string, chapterContext?: string): Promise<AuditResponse> {
    return this.fetch('/auditor/evaluate', {
      method: 'POST',
      body: JSON.stringify({
        text,
        chapter_context: chapterContext
      }),
    });
  }

  async getCriteria(): Promise<unknown> {
    return this.fetch('/auditor/criteria');
  }

  // DNA Engine
  async analyzeDNA(): Promise<DNAProfile> {
    return this.fetch('/dna/analyze', {
      method: 'POST',
    });
  }

  async getDNAProfile(): Promise<unknown> {
    return this.fetch('/dna/profile');
  }

  // Red Thread
  async checkConsistency(text: string): Promise<RedThreadCheckResponse> {
    return this.fetch('/red-thread/check', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  }

  async indexChapters(): Promise<unknown> {
    return this.fetch('/red-thread/index', {
      method: 'POST',
    });
  }

  async getRedThreadStats(): Promise<RedThreadStats> {
    return this.fetch('/red-thread/stats');
  }

  // Usage Stats
  async getUsageStats(): Promise<unknown> {
    return this.fetch('/stats/usage');
  }
}

// Export a singleton instance
export const api = new PHDxAPIClient();
