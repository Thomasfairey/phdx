'use client';

import { useState } from 'react';
import { Shield, ShieldCheck, ShieldAlert, Loader2, Send } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SanitizeResponse {
  sanitized_text: string;
  pii_found: boolean;
}

export function AirlockModule() {
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState<SanitizeResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSanitize = async () => {
    if (!inputText.trim()) return;

    setIsProcessing(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/airlock/sanitize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText })
      });

      if (!res.ok) throw new Error('Sanitization failed');

      const data: SanitizeResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    }

    setIsProcessing(false);
  };

  const renderHighlightedText = (text: string) => {
    const parts = text.split(/(\[REDACTED\])/g);
    return parts.map((part, index) => {
      if (part === '[REDACTED]') {
        return (
          <span
            key={index}
            className="bg-red-500/30 text-red-400 px-1 rounded font-mono"
          >
            {part}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            Airlock
          </h2>
          <p className="text-[#8A8F98] mt-1">PII Detection & Sanitization Engine</p>
        </div>

        {/* Status Badge */}
        {result && (
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
            result.pii_found
              ? 'bg-red-500/20 border border-red-500/30'
              : 'bg-green-500/20 border border-green-500/30'
          }`}>
            {result.pii_found ? (
              <>
                <ShieldAlert className="w-5 h-5 text-red-400" />
                <span className="text-red-400 font-medium">PII Detected</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-5 h-5 text-green-400" />
                <span className="text-green-400 font-medium">Safe</span>
              </>
            )}
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
          placeholder="Paste your text here to scan for PII (names, emails, phone numbers, addresses, etc.)..."
          className="w-full h-40 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-[#8A8F98]/50 focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all"
        />

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleSanitize}
            disabled={isProcessing || !inputText.trim()}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-cyan-500/20"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Scanning...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Sanitize
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

      {/* Output Section */}
      {result && (
        <div className="glass-panel p-6">
          <div className="flex items-center justify-between mb-4">
            <label className="block text-sm font-medium text-[#8A8F98]">
              Sanitized Output
            </label>
            {result.pii_found && (
              <span className="text-xs text-red-400 bg-red-500/20 px-2 py-1 rounded-full">
                Redacted content highlighted
              </span>
            )}
          </div>
          <div className="bg-black/40 border border-white/10 rounded-xl p-4 min-h-[160px]">
            <p className="text-white whitespace-pre-wrap leading-relaxed">
              {renderHighlightedText(result.sanitized_text)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
