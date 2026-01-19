'use client';

import { useState } from 'react';
import { Link2, Loader2, ArrowRight } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RedThreadResponse {
  continuity_score: number;
  status: string;
  analysis: string;
}

export function RedThreadModule() {
  const [introduction, setIntroduction] = useState('');
  const [discussion, setDiscussion] = useState('');
  const [result, setResult] = useState<RedThreadResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCheck = async () => {
    if (!introduction.trim() || !discussion.trim()) return;

    setIsProcessing(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/red-thread/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ introduction, discussion })
      });

      if (!res.ok) throw new Error('Continuity check failed');

      const data: RedThreadResponse = await res.json();
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

  const scoreColors = result ? getScoreColor(result.continuity_score) : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center">
            <Link2 className="w-5 h-5 text-white" />
          </div>
          Red Thread
        </h2>
        <p className="text-[#8A8F98] mt-1">Thesis Continuity & Argument Flow Analysis</p>
      </div>

      {/* Input Sections */}
      <div className="grid grid-cols-2 gap-6">
        {/* Introduction */}
        <div className="glass-panel p-6">
          <label className="block text-sm font-medium text-[#8A8F98] mb-3">
            Introduction
          </label>
          <textarea
            value={introduction}
            onChange={(e) => setIntroduction(e.target.value)}
            placeholder="Paste your introduction section here..."
            className="w-full h-48 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-[#8A8F98]/50 focus:border-red-500/50 focus:ring-2 focus:ring-red-500/20 transition-all"
          />
          <p className="mt-2 text-xs text-[#8A8F98]">
            {introduction.length} characters
          </p>
        </div>

        {/* Discussion */}
        <div className="glass-panel p-6">
          <label className="block text-sm font-medium text-[#8A8F98] mb-3">
            Discussion
          </label>
          <textarea
            value={discussion}
            onChange={(e) => setDiscussion(e.target.value)}
            placeholder="Paste your discussion section here..."
            className="w-full h-48 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-[#8A8F98]/50 focus:border-orange-500/50 focus:ring-2 focus:ring-orange-500/20 transition-all"
          />
          <p className="mt-2 text-xs text-[#8A8F98]">
            {discussion.length} characters
          </p>
        </div>
      </div>

      {/* Action Button */}
      <div className="flex justify-center">
        <button
          onClick={handleCheck}
          disabled={isProcessing || !introduction.trim() || !discussion.trim()}
          className="flex items-center gap-3 px-8 py-3 bg-gradient-to-r from-red-500 to-orange-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-red-500/20"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Checking Continuity...
            </>
          ) : (
            <>
              <Link2 className="w-5 h-5" />
              Check Continuity
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>
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
                {/* Background circle */}
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
                    strokeDasharray={`${result.continuity_score * 3.52} 352`}
                    className={scoreColors.text}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="text-center">
                  <span className={`text-4xl font-bold ${scoreColors.text}`}>
                    {Math.round(result.continuity_score)}
                  </span>
                  <span className={`text-lg ${scoreColors.text}`}>%</span>
                </div>
              </div>
              <p className="text-center text-sm text-[#8A8F98] mt-3">Continuity Score</p>
            </div>

            {/* Analysis */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  result.continuity_score < 30
                    ? 'bg-red-500/20 text-red-400'
                    : result.continuity_score < 70
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'bg-green-500/20 text-green-400'
                }`}>
                  {result.status}
                </span>
              </div>

              <h3 className="text-sm font-medium text-[#8A8F98] mb-2">Analysis</h3>
              <div className="bg-black/30 rounded-xl p-4 border border-white/5">
                <p className="text-white leading-relaxed">{result.analysis}</p>
              </div>

              {/* Score Legend */}
              <div className="mt-4 flex items-center gap-6 text-xs text-[#8A8F98]">
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
