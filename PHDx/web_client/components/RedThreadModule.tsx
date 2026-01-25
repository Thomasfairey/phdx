'use client';

import { useState, useEffect } from 'react';
import { Link2, Loader2, Send, Database, RefreshCw, BookOpen } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface IndexStats {
  total_chunks?: number;
  chapters_indexed?: string[];
  last_indexed?: string;
  status?: string;
}

interface ConsistencyReport {
  overall_score?: number;
  status?: string;
  consistency_analysis?: string;
  issues?: string[];
  suggestions?: string[];
  cross_references?: {
    term: string;
    occurrences: number;
  }[];
}

export function RedThreadModule() {
  const [inputText, setInputText] = useState('');
  const [stats, setStats] = useState<IndexStats | null>(null);
  const [result, setResult] = useState<ConsistencyReport | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load stats on mount
  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setIsLoadingStats(true);
    try {
      const res = await fetch(`${API_URL}/red-thread/stats`);
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
    setIsLoadingStats(false);
  };

  const handleIndex = async () => {
    setIsIndexing(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/red-thread/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Indexing failed');
      }

      await loadStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Indexing failed');
    }

    setIsIndexing(false);
  };

  const handleCheck = async () => {
    if (!inputText.trim() || inputText.length < 50) return;

    setIsProcessing(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/red-thread/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Consistency check failed');
      }

      const data: ConsistencyReport = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    }

    setIsProcessing(false);
  };

  const getScoreColor = (score: number) => {
    if (score < 30) return { bg: 'bg-red-500', text: 'text-red-400', ring: 'ring-red-500/30' };
    if (score < 70) return { bg: 'bg-amber-500', text: 'text-amber-400', ring: 'ring-amber-500/30' };
    return { bg: 'bg-green-500', text: 'text-green-400', ring: 'ring-green-500/30' };
  };

  const scoreColors = result?.overall_score ? getScoreColor(result.overall_score) : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center">
              <Link2 className="w-5 h-5 text-white" />
            </div>
            Red Thread
          </h2>
          <p className="text-[#8A8F98] mt-1">Thesis Continuity & Argument Flow Analysis</p>
        </div>

        {/* Index Status */}
        {stats && stats.total_chunks && stats.total_chunks > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-orange-500/20 border border-orange-500/30">
            <Database className="w-5 h-5 text-orange-400" />
            <span className="text-orange-400 font-medium">{stats.total_chunks} Chunks Indexed</span>
          </div>
        )}
      </div>

      {/* Index Management */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">Thesis Index</h3>
            <p className="text-sm text-[#8A8F98] mt-1">
              Index your thesis chapters to enable consistency checking
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={loadStats}
              disabled={isLoadingStats}
              className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 text-white rounded-xl hover:bg-white/10 disabled:opacity-40 transition-all"
            >
              {isLoadingStats ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Refresh
            </button>
            <button
              onClick={handleIndex}
              disabled={isIndexing}
              className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-orange-500 to-red-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-orange-500/20"
            >
              {isIndexing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Indexing...
                </>
              ) : (
                <>
                  <BookOpen className="w-4 h-4" />
                  Index Chapters
                </>
              )}
            </button>
          </div>
        </div>

        {/* Stats Display */}
        {stats && (
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="bg-black/30 rounded-xl p-4 border border-white/5">
              <p className="text-2xl font-bold text-white">{stats.total_chunks || 0}</p>
              <p className="text-xs text-[#8A8F98] mt-1">Text Chunks</p>
            </div>
            <div className="bg-black/30 rounded-xl p-4 border border-white/5">
              <p className="text-2xl font-bold text-white">{stats.chapters_indexed?.length || 0}</p>
              <p className="text-xs text-[#8A8F98] mt-1">Chapters</p>
            </div>
            <div className="bg-black/30 rounded-xl p-4 border border-white/5">
              <p className="text-sm font-medium text-white truncate">
                {stats.last_indexed ? new Date(stats.last_indexed).toLocaleDateString() : 'Never'}
              </p>
              <p className="text-xs text-[#8A8F98] mt-1">Last Indexed</p>
            </div>
          </div>
        )}

        {/* Chapters List */}
        {stats?.chapters_indexed && stats.chapters_indexed.length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-[#8A8F98] mb-2">Indexed chapters:</p>
            <div className="flex flex-wrap gap-2">
              {stats.chapters_indexed.map((ch, i) => (
                <span key={i} className="px-2 py-1 bg-orange-500/20 text-orange-300 rounded text-xs">
                  {ch}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Input Section */}
      <div className="glass-panel p-6">
        <label className="block text-sm font-medium text-[#8A8F98] mb-3">
          Text to Check (min 50 characters)
        </label>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste a section of your thesis to check for consistency with indexed content..."
          className="w-full h-48 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-[#8A8F98]/50 focus:border-red-500/50 focus:ring-2 focus:ring-red-500/20 transition-all"
        />
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-[#8A8F98]">{inputText.length} characters</p>
          <button
            onClick={handleCheck}
            disabled={isProcessing || inputText.length < 50}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-red-500 to-orange-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-red-500/20"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Checking...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Check Consistency
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="glass-panel p-4 border-red-500/30 bg-red-500/10">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Results Section */}
      {result && scoreColors && (
        <div className="glass-panel p-6">
          <div className="flex items-start gap-8">
            {/* Score Circle */}
            <div className="flex-shrink-0">
              <div className={`relative w-32 h-32 rounded-full ring-4 ${scoreColors.ring} flex items-center justify-center`}>
                <svg className="absolute inset-0 w-full h-full -rotate-90">
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="none"
                    className="text-white/5"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={`${(result.overall_score || 0) * 3.52} 352`}
                    className={scoreColors.text}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="text-center">
                  <span className={`text-4xl font-bold ${scoreColors.text}`}>
                    {Math.round(result.overall_score || 0)}
                  </span>
                  <span className={`text-lg ${scoreColors.text}`}>%</span>
                </div>
              </div>
              <p className="text-center text-sm text-[#8A8F98] mt-3">Consistency Score</p>
            </div>

            {/* Analysis */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  (result.overall_score || 0) < 30
                    ? 'bg-red-500/20 text-red-400'
                    : (result.overall_score || 0) < 70
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'bg-green-500/20 text-green-400'
                }`}>
                  {result.status || 'Analyzed'}
                </span>
              </div>

              {result.consistency_analysis && (
                <>
                  <h3 className="text-sm font-medium text-[#8A8F98] mb-2">Analysis</h3>
                  <div className="bg-black/30 rounded-xl p-4 border border-white/5 mb-4">
                    <p className="text-white leading-relaxed">{result.consistency_analysis}</p>
                  </div>
                </>
              )}

              {/* Issues */}
              {result.issues && result.issues.length > 0 && (
                <>
                  <h3 className="text-sm font-medium text-[#8A8F98] mb-2">Issues Found</h3>
                  <ul className="space-y-2 mb-4">
                    {result.issues.map((issue, i) => (
                      <li key={i} className="flex items-start gap-2 text-amber-300 text-sm">
                        <span className="text-amber-500 mt-1">•</span>
                        {issue}
                      </li>
                    ))}
                  </ul>
                </>
              )}

              {/* Suggestions */}
              {result.suggestions && result.suggestions.length > 0 && (
                <>
                  <h3 className="text-sm font-medium text-[#8A8F98] mb-2">Suggestions</h3>
                  <ul className="space-y-2">
                    {result.suggestions.map((sug, i) => (
                      <li key={i} className="flex items-start gap-2 text-green-300 text-sm">
                        <span className="text-green-500 mt-1">✓</span>
                        {sug}
                      </li>
                    ))}
                  </ul>
                </>
              )}

              {/* Score Legend */}
              <div className="mt-6 flex items-center gap-6 text-xs text-[#8A8F98]">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span>Poor (&lt;30%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <span>Fair (30-70%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span>Strong (&gt;70%)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
