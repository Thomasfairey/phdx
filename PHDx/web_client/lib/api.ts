/**
 * PHDx API Client Library
 *
 * Type definitions and API client for the PHDx FastAPI backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
