'use client';

import { useState } from 'react';
import { ClipboardCheck, Loader2, Send, CheckCircle, XCircle } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AuditorResponse {
  total_weighted_score: number;
  pass_status: boolean;
}

export function AuditorModule() {
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState<AuditorResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleScore = async () => {
    if (!inputText.trim()) return;

    setIsProcessing(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/auditor/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText })
      });

      if (!res.ok) throw new Error('Scoring failed');

      const data: AuditorResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    }

    setIsProcessing(false);
  };

  const getScoreGrade = (score: number) => {
    if (score >= 90) return { grade: 'A+', color: 'text-green-400' };
    if (score >= 80) return { grade: 'A', color: 'text-green-400' };
    if (score >= 70) return { grade: 'B', color: 'text-emerald-400' };
    if (score >= 60) return { grade: 'C', color: 'text-amber-400' };
    if (score >= 50) return { grade: 'D', color: 'text-orange-400' };
    return { grade: 'F', color: 'text-red-400' };
  };

  const gradeInfo = result ? getScoreGrade(result.total_weighted_score) : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
              <ClipboardCheck className="w-5 h-5 text-white" />
            </div>
            Auditor
          </h2>
          <p className="text-[#8A8F98] mt-1">Quality Assessment & Scoring Engine</p>
        </div>

        {/* Pass/Fail Badge */}
        {result && (
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
            result.pass_status
              ? 'bg-green-500/20 border border-green-500/30'
              : 'bg-red-500/20 border border-red-500/30'
          }`}>
            {result.pass_status ? (
              <>
                <CheckCircle className="w-5 h-5 text-green-400" />
                <span className="text-green-400 font-medium">PASS</span>
              </>
            ) : (
              <>
                <XCircle className="w-5 h-5 text-red-400" />
                <span className="text-red-400 font-medium">FAIL</span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Input Section */}
      <div className="glass-panel p-6">
        <label className="block text-sm font-medium text-[#8A8F98] mb-3">
          Document Text
        </label>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste your thesis content here for quality assessment..."
          className="w-full h-48 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-[#8A8F98]/50 focus:border-green-500/50 focus:ring-2 focus:ring-green-500/20 transition-all"
        />

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleScore}
            disabled={isProcessing || !inputText.trim()}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-green-500/20"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Scoring...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Run Audit
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
      {result && gradeInfo && (
        <div className="glass-panel p-6">
          <label className="block text-sm font-medium text-[#8A8F98] mb-6">
            Quality Assessment Results
          </label>

          <div className="grid grid-cols-3 gap-6">
            {/* Score Display */}
            <div className="col-span-2 bg-black/30 rounded-xl p-6 border border-white/5">
              <div className="flex items-center gap-8">
                {/* Score Circle */}
                <div className="relative w-36 h-36">
                  <svg className="w-full h-full -rotate-90">
                    <circle
                      cx="72"
                      cy="72"
                      r="64"
                      stroke="currentColor"
                      strokeWidth="10"
                      fill="none"
                      className="text-white/5"
                    />
                    <circle
                      cx="72"
                      cy="72"
                      r="64"
                      stroke="currentColor"
                      strokeWidth="10"
                      fill="none"
                      strokeDasharray={`${result.total_weighted_score * 4.02} 402`}
                      className={result.pass_status ? 'text-green-400' : 'text-red-400'}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className={`text-4xl font-bold ${result.pass_status ? 'text-green-400' : 'text-red-400'}`}>
                      {result.total_weighted_score.toFixed(1)}
                    </span>
                  </div>
                </div>

                {/* Score Breakdown */}
                <div className="flex-1">
                  <p className="text-sm text-[#8A8F98] mb-2">Weighted Score</p>
                  <div className="h-3 bg-black/40 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        result.pass_status
                          ? 'bg-gradient-to-r from-green-500 to-emerald-400'
                          : 'bg-gradient-to-r from-red-500 to-orange-400'
                      }`}
                      style={{ width: `${result.total_weighted_score}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-2 text-xs text-[#8A8F98]">
                    <span>0</span>
                    <span>50</span>
                    <span>100</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Grade Display */}
            <div className="bg-black/30 rounded-xl p-6 border border-white/5 flex flex-col items-center justify-center">
              <span className={`text-6xl font-bold ${gradeInfo.color}`}>
                {gradeInfo.grade}
              </span>
              <p className="text-sm text-[#8A8F98] mt-2">Grade</p>
            </div>
          </div>

          {/* Threshold Indicator */}
          <div className="mt-6 pt-6 border-t border-white/5">
            <div className="flex items-center justify-between text-sm">
              <span className="text-[#8A8F98]">Pass Threshold: 70%</span>
              <span className={result.pass_status ? 'text-green-400' : 'text-red-400'}>
                {result.pass_status
                  ? `+${(result.total_weighted_score - 70).toFixed(1)} above threshold`
                  : `${(result.total_weighted_score - 70).toFixed(1)} below threshold`
                }
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
