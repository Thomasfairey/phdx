'use client';

import { useState } from 'react';
import { ClipboardCheck, Loader2, Send, CheckCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface CriteriaScore {
  score: number;
  level: string;
  feedback: string;
}

interface AuditResponse {
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
    originality: CriteriaScore;
    criticality: CriteriaScore;
    rigour: CriteriaScore;
  };
  strengths: string[];
  areas_for_improvement: string[];
  specific_recommendations: string[];
  examiner_summary: string;
  error?: string;
}

export function AuditorModule() {
  const [inputText, setInputText] = useState('');
  const [chapterContext, setChapterContext] = useState('General Draft');
  const [result, setResult] = useState<AuditResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const chapters = [
    'General Draft',
    'Chapter 1: Introduction',
    'Chapter 2: Literature Review',
    'Chapter 3: Methodology',
    'Chapter 4: Findings/Results',
    'Chapter 5: Discussion',
    'Chapter 6: Conclusion',
    'Abstract'
  ];

  const handleAudit = async () => {
    if (!inputText.trim() || inputText.length < 100) return;

    setIsProcessing(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/auditor/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: inputText,
          chapter_context: chapterContext
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Audit failed');
      }

      const data: AuditResponse = await res.json();
      if (data.error) {
        throw new Error(data.error);
      }
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    }

    setIsProcessing(false);
  };

  const getLevelColor = (level: string) => {
    const colors: Record<string, { bg: string; text: string; border: string }> = {
      excellent: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' },
      good: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30' },
      satisfactory: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' },
      needs_improvement: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30' },
      unsatisfactory: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' }
    };
    return colors[level] || colors.satisfactory;
  };

  const getScoreGrade = (score: number) => {
    if (score >= 85) return { grade: 'A+', color: 'text-green-400' };
    if (score >= 70) return { grade: 'A', color: 'text-blue-400' };
    if (score >= 60) return { grade: 'B', color: 'text-amber-400' };
    if (score >= 50) return { grade: 'C', color: 'text-orange-400' };
    return { grade: 'F', color: 'text-red-400' };
  };

  const passStatus = result ? result.overall_grade.score >= 60 : false;
  const gradeInfo = result ? getScoreGrade(result.overall_grade.score) : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
              <ClipboardCheck className="w-5 h-5 text-white" />
            </div>
            Brookes Auditor
          </h2>
          <p className="text-[#8A8F98] mt-1">Oxford Brookes PhD Marking Criteria Evaluator</p>
        </div>

        {/* Pass/Fail Badge */}
        {result && result.status === 'success' && (
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
            passStatus
              ? 'bg-green-500/20 border border-green-500/30'
              : 'bg-red-500/20 border border-red-500/30'
          }`}>
            {passStatus ? (
              <>
                <CheckCircle className="w-5 h-5 text-green-400" />
                <span className="text-green-400 font-medium">PASS</span>
              </>
            ) : (
              <>
                <XCircle className="w-5 h-5 text-red-400" />
                <span className="text-red-400 font-medium">NEEDS WORK</span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Input Section */}
      <div className="glass-panel p-6">
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-[#8A8F98] mb-2">
              Chapter Context
            </label>
            <select
              value={chapterContext}
              onChange={(e) => setChapterContext(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-white focus:border-green-500/50 focus:ring-2 focus:ring-green-500/20 transition-all"
            >
              {chapters.map(ch => (
                <option key={ch} value={ch}>{ch}</option>
              ))}
            </select>
          </div>
          <div className="text-sm text-[#8A8F98] self-end pb-2">
            {inputText.length} chars (min 100)
          </div>
        </div>

        <label className="block text-sm font-medium text-[#8A8F98] mb-3">
          Thesis Draft
        </label>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste your thesis content here for evaluation against Oxford Brookes marking criteria (minimum 100 characters)..."
          className="w-full h-48 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-[#8A8F98]/50 focus:border-green-500/50 focus:ring-2 focus:ring-green-500/20 transition-all"
        />

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleAudit}
            disabled={isProcessing || inputText.length < 100}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-green-500/20"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Evaluating...
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
      {result && result.status === 'success' && gradeInfo && (
        <div className="space-y-6">
          {/* Overall Score */}
          <div className="glass-panel p-6">
            <div className="grid grid-cols-4 gap-6">
              {/* Score Circle */}
              <div className="col-span-1 flex flex-col items-center justify-center">
                <div className="relative w-32 h-32">
                  <svg className="w-full h-full -rotate-90">
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="currentColor"
                      strokeWidth="10"
                      fill="none"
                      className="text-white/5"
                    />
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="currentColor"
                      strokeWidth="10"
                      fill="none"
                      strokeDasharray={`${result.overall_grade.score * 3.52} 352`}
                      className={passStatus ? 'text-green-400' : 'text-red-400'}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className={`text-3xl font-bold ${passStatus ? 'text-green-400' : 'text-red-400'}`}>
                      {result.overall_grade.score}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-[#8A8F98] mt-2">Overall Score</p>
              </div>

              {/* Grade & Level */}
              <div className="col-span-1 flex flex-col items-center justify-center bg-black/30 rounded-xl border border-white/5">
                <span className={`text-5xl font-bold ${gradeInfo.color}`}>
                  {gradeInfo.grade}
                </span>
                <p className={`text-sm mt-2 ${getLevelColor(result.overall_grade.level).text}`}>
                  {result.overall_grade.level.replace('_', ' ').toUpperCase()}
                </p>
              </div>

              {/* Descriptor */}
              <div className="col-span-2 flex flex-col justify-center bg-black/30 rounded-xl p-4 border border-white/5">
                <p className="text-white leading-relaxed">{result.overall_grade.descriptor}</p>
                <div className="mt-3 flex items-center gap-2 text-xs text-[#8A8F98]">
                  <span>Audit ID: {result.audit_id}</span>
                  <span>|</span>
                  <span>{result.word_count.toLocaleString()} words</span>
                  <span>|</span>
                  <span>{result.context}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Criteria Breakdown */}
          <div className="glass-panel p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Criteria Breakdown</h3>
            <div className="grid grid-cols-3 gap-4">
              {(['originality', 'criticality', 'rigour'] as const).map(criterion => {
                const data = result.criteria_scores[criterion];
                const colors = getLevelColor(data.level);
                const weight = criterion === 'rigour' ? '30%' : '35%';
                const label = criterion === 'criticality' ? 'Critical Analysis' :
                              criterion === 'rigour' ? 'Methodological Rigour' :
                              'Originality';
                return (
                  <div key={criterion} className={`rounded-xl p-4 ${colors.bg} border ${colors.border}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-[#8A8F98]">{label}</span>
                      <span className="text-xs text-[#8A8F98]">{weight}</span>
                    </div>
                    <div className={`text-3xl font-bold ${colors.text}`}>
                      {data.score}/100
                    </div>
                    <p className="text-xs text-white/70 mt-2 line-clamp-3">{data.feedback}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Strengths & Improvements */}
          <div className="grid grid-cols-2 gap-6">
            <div className="glass-panel p-6">
              <h3 className="text-lg font-semibold text-green-400 mb-4">Strengths</h3>
              <ul className="space-y-2">
                {result.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-white/80">
                    <CheckCircle className="w-4 h-4 text-green-400 mt-1 flex-shrink-0" />
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="glass-panel p-6">
              <h3 className="text-lg font-semibold text-amber-400 mb-4">Areas for Improvement</h3>
              <ul className="space-y-2">
                {result.areas_for_improvement.map((a, i) => (
                  <li key={i} className="flex items-start gap-2 text-white/80">
                    <XCircle className="w-4 h-4 text-amber-400 mt-1 flex-shrink-0" />
                    <span>{a}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Recommendations */}
          <div className="glass-panel p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recommendations</h3>
            <ol className="space-y-3">
              {result.specific_recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-3 text-white/80">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-sm font-medium">
                    {i + 1}
                  </span>
                  <span>{rec}</span>
                </li>
              ))}
            </ol>
          </div>

          {/* Examiner Summary (Collapsible) */}
          <div className="glass-panel">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="w-full p-6 flex items-center justify-between text-left"
            >
              <h3 className="text-lg font-semibold text-white">Examiner Summary</h3>
              {showDetails ? (
                <ChevronUp className="w-5 h-5 text-[#8A8F98]" />
              ) : (
                <ChevronDown className="w-5 h-5 text-[#8A8F98]" />
              )}
            </button>
            {showDetails && (
              <div className="px-6 pb-6">
                <div className="bg-black/30 rounded-xl p-4 border border-white/5">
                  <p className="text-white/80 whitespace-pre-wrap leading-relaxed">
                    {result.examiner_summary}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
