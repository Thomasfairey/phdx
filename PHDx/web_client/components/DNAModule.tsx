'use client';

import { useState } from 'react';
import { Activity, Bot, User, Loader2, Send } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DNAResponse {
  variance: number;
  style_match: boolean;
  status: string;
}

export function DNAModule() {
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState<DNAResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!inputText.trim()) return;

    setIsProcessing(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/dna/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText })
      });

      if (!res.ok) throw new Error('Analysis failed');

      const data: DNAResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    }

    setIsProcessing(false);
  };

  const getVarianceLabel = (variance: number) => {
    if (variance < 5.0) return { label: 'Robotic / AI', icon: Bot, color: 'red' };
    if (variance > 10.0) return { label: 'Human', icon: User, color: 'green' };
    return { label: 'Mixed', icon: Activity, color: 'amber' };
  };

  const getGaugeColor = (variance: number) => {
    if (variance < 5.0) return 'from-red-500 to-orange-500';
    if (variance > 10.0) return 'from-green-400 to-emerald-500';
    return 'from-amber-400 to-yellow-500';
  };

  const varianceInfo = result ? getVarianceLabel(result.variance) : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            DNA Analyzer
          </h2>
          <p className="text-[#8A8F98] mt-1">Writing Style & Variance Detection</p>
        </div>

        {/* Status Badge */}
        {varianceInfo && (
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
            varianceInfo.color === 'red'
              ? 'bg-red-500/20 border border-red-500/30'
              : varianceInfo.color === 'green'
              ? 'bg-green-500/20 border border-green-500/30'
              : 'bg-amber-500/20 border border-amber-500/30'
          }`}>
            <varianceInfo.icon className={`w-5 h-5 ${
              varianceInfo.color === 'red' ? 'text-red-400' :
              varianceInfo.color === 'green' ? 'text-green-400' : 'text-amber-400'
            }`} />
            <span className={`font-medium ${
              varianceInfo.color === 'red' ? 'text-red-400' :
              varianceInfo.color === 'green' ? 'text-green-400' : 'text-amber-400'
            }`}>
              {varianceInfo.label}
            </span>
          </div>
        )}
      </div>

      {/* Input Section */}
      <div className="glass-panel p-6">
        <label className="block text-sm font-medium text-[#8A8F98] mb-3">
          Input Text
        </label>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste your text here to analyze writing style variance..."
          className="w-full h-40 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-[#8A8F98]/50 focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all"
        />

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleAnalyze}
            disabled={isProcessing || !inputText.trim()}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-500/20"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Analyze DNA
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
      {result && (
        <div className="glass-panel p-6">
          <label className="block text-sm font-medium text-[#8A8F98] mb-6">
            Variance Analysis
          </label>

          {/* Variance Gauge */}
          <div className="mb-8">
            <div className="flex justify-between text-xs text-[#8A8F98] mb-2">
              <span>AI / Robotic</span>
              <span>Mixed</span>
              <span>Human</span>
            </div>
            <div className="relative h-4 bg-black/40 rounded-full overflow-hidden border border-white/10">
              {/* Gauge markers */}
              <div className="absolute inset-0 flex">
                <div className="flex-1 border-r border-white/10" />
                <div className="flex-1 border-r border-white/10" />
                <div className="flex-1" />
              </div>
              {/* Gauge fill */}
              <div
                className={`absolute left-0 top-0 h-full bg-gradient-to-r ${getGaugeColor(result.variance)} rounded-full transition-all duration-500`}
                style={{ width: `${Math.min(result.variance * 6.67, 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-[#8A8F98] mt-2">
              <span>0</span>
              <span>5</span>
              <span>10</span>
              <span>15</span>
            </div>
          </div>

          {/* Score Display */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-black/30 rounded-xl p-4 text-center border border-white/5">
              <p className="text-3xl font-bold text-white">{result.variance.toFixed(2)}</p>
              <p className="text-xs text-[#8A8F98] mt-1">Variance Score</p>
            </div>
            <div className="bg-black/30 rounded-xl p-4 text-center border border-white/5">
              <p className={`text-3xl font-bold ${result.style_match ? 'text-green-400' : 'text-red-400'}`}>
                {result.style_match ? 'Yes' : 'No'}
              </p>
              <p className="text-xs text-[#8A8F98] mt-1">Style Match</p>
            </div>
            <div className="bg-black/30 rounded-xl p-4 text-center border border-white/5">
              <p className="text-3xl font-bold text-[#64D2FF]">{result.status}</p>
              <p className="text-xs text-[#8A8F98] mt-1">Status</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
