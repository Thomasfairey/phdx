'use client';

import { useState, useEffect } from 'react';
import { Activity, Loader2, RefreshCw, Database, FileText } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DNAProfile {
  total_words_analyzed?: number;
  avg_sentence_length?: number;
  avg_word_length?: number;
  vocabulary_richness?: number;
  hedging_frequency?: number;
  formality_score?: number;
  sample_transitions?: string[];
  sample_hedges?: string[];
  analyzed_at?: string;
}

interface DNAResponse {
  success: boolean;
  profile?: DNAProfile;
  error?: string;
}

export function DNAModule() {
  const [profile, setProfile] = useState<DNAProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load existing profile on mount
  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/dna/profile`);
      const data = await res.json();

      if (data.error) {
        // No profile exists yet - that's okay
        setProfile(null);
      } else {
        setProfile(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    }

    setIsLoading(false);
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/dna/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Analysis failed');
      }

      const data: DNAResponse = await res.json();
      if (!data.success) {
        throw new Error(data.error || 'Analysis failed');
      }

      // Reload profile after analysis
      await loadProfile();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    }

    setIsAnalyzing(false);
  };

  const getScoreColor = (score: number, thresholds: { low: number; high: number }) => {
    if (score < thresholds.low) return 'text-red-400';
    if (score > thresholds.high) return 'text-green-400';
    return 'text-amber-400';
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            DNA Engine
          </h2>
          <p className="text-[#8A8F98] mt-1">Linguistic Fingerprint & Writing Style Analysis</p>
        </div>

        {/* Profile Status */}
        {profile && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/20 border border-purple-500/30">
            <Database className="w-5 h-5 text-purple-400" />
            <span className="text-purple-400 font-medium">Profile Active</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">Writing Style Analysis</h3>
            <p className="text-sm text-[#8A8F98] mt-1">
              Analyze documents in your drafts folder to build your linguistic fingerprint
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={loadProfile}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 text-white rounded-xl hover:bg-white/10 disabled:opacity-40 transition-all"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Refresh
            </button>
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-500/20"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4" />
                  Analyze Drafts
                </>
              )}
            </button>
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-4">
          <p className="text-sm text-purple-300">
            The DNA Engine analyzes your existing thesis drafts to create a unique linguistic fingerprint.
            This profile helps maintain consistent voice and style across your writing.
            Place your draft documents (.docx, .pdf, .txt) in the <code className="bg-black/30 px-1 rounded">drafts/</code> folder.
          </p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="glass-panel p-4 border-red-500/30 bg-red-500/10">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && !profile && (
        <div className="glass-panel p-12 flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
        </div>
      )}

      {/* No Profile State */}
      {!isLoading && !profile && !error && (
        <div className="glass-panel p-12 text-center">
          <Activity className="w-16 h-16 text-[#8A8F98]/30 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">No DNA Profile Found</h3>
          <p className="text-[#8A8F98] mb-6">
            Run the analysis to build your linguistic fingerprint from your drafts
          </p>
        </div>
      )}

      {/* Profile Display */}
      {profile && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-3 gap-4">
            <div className="glass-panel p-6 text-center">
              <p className="text-4xl font-bold text-white">
                {profile.total_words_analyzed?.toLocaleString() || 0}
              </p>
              <p className="text-sm text-[#8A8F98] mt-2">Words Analyzed</p>
            </div>
            <div className="glass-panel p-6 text-center">
              <p className={`text-4xl font-bold ${getScoreColor(profile.avg_sentence_length || 0, { low: 15, high: 30 })}`}>
                {profile.avg_sentence_length?.toFixed(1) || 0}
              </p>
              <p className="text-sm text-[#8A8F98] mt-2">Avg Sentence Length</p>
            </div>
            <div className="glass-panel p-6 text-center">
              <p className={`text-4xl font-bold ${getScoreColor(profile.vocabulary_richness || 0, { low: 0.3, high: 0.6 })}`}>
                {formatPercent(profile.vocabulary_richness || 0)}
              </p>
              <p className="text-sm text-[#8A8F98] mt-2">Vocabulary Richness</p>
            </div>
          </div>

          {/* Detailed Analysis */}
          <div className="glass-panel p-6">
            <h3 className="text-lg font-semibold text-white mb-6">Style Metrics</h3>

            <div className="space-y-6">
              {/* Hedging Frequency */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-[#8A8F98]">Hedging Frequency</span>
                  <span className={`font-medium ${getScoreColor(profile.hedging_frequency || 0, { low: 0.02, high: 0.08 })}`}>
                    {formatPercent(profile.hedging_frequency || 0)}
                  </span>
                </div>
                <div className="h-2 bg-black/40 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min((profile.hedging_frequency || 0) * 1000, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-[#8A8F98] mt-1">
                  Academic hedging (suggests, arguably, potentially) - ideal range: 2-8%
                </p>
              </div>

              {/* Formality Score */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-[#8A8F98]">Formality Score</span>
                  <span className={`font-medium ${getScoreColor(profile.formality_score || 0, { low: 0.5, high: 0.8 })}`}>
                    {formatPercent(profile.formality_score || 0)}
                  </span>
                </div>
                <div className="h-2 bg-black/40 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full transition-all duration-500"
                    style={{ width: `${(profile.formality_score || 0) * 100}%` }}
                  />
                </div>
                <p className="text-xs text-[#8A8F98] mt-1">
                  Academic formality level - ideal for PhD: 70-90%
                </p>
              </div>

              {/* Word Length */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-[#8A8F98]">Average Word Length</span>
                  <span className="font-medium text-white">
                    {profile.avg_word_length?.toFixed(2) || 0} chars
                  </span>
                </div>
                <div className="h-2 bg-black/40 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min((profile.avg_word_length || 0) * 10, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Sample Phrases */}
          {(profile.sample_hedges?.length || profile.sample_transitions?.length) && (
            <div className="grid grid-cols-2 gap-6">
              {profile.sample_hedges && profile.sample_hedges.length > 0 && (
                <div className="glass-panel p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Sample Hedges</h3>
                  <div className="flex flex-wrap gap-2">
                    {profile.sample_hedges.slice(0, 10).map((hedge, i) => (
                      <span key={i} className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full text-sm">
                        {hedge}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {profile.sample_transitions && profile.sample_transitions.length > 0 && (
                <div className="glass-panel p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Sample Transitions</h3>
                  <div className="flex flex-wrap gap-2">
                    {profile.sample_transitions.slice(0, 10).map((trans, i) => (
                      <span key={i} className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm">
                        {trans}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Last Analyzed */}
          {profile.analyzed_at && (
            <div className="text-center text-sm text-[#8A8F98]">
              Last analyzed: {new Date(profile.analyzed_at).toLocaleString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
