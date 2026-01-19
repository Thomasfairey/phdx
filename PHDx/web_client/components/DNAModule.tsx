'use client';

import { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  Loader2,
  Send,
  Check,
  X,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Sparkles,
  RotateCcw,
  Copy,
  CheckCheck,
  Info
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// Type Definitions
// =============================================================================

interface StyleEdit {
  original: string;
  suggested: string;
  reason: string;
  category: 'hedging' | 'clarity' | 'conciseness' | 'tone' | 'grammar';
  start_index: number;
  end_index: number;
}

interface StyleMetrics {
  sentence_complexity?: {
    average_length: number;
    total_sentences: number;
  };
  hedging?: {
    hedging_density_per_1000_words: number;
    total_hedges: number;
  };
  transitions?: {
    preferred_categories: string[];
  };
}

interface DNAStyleResponse {
  original_text: string;
  improved_text: string;
  edits: StyleEdit[];
  style_metrics: StyleMetrics;
  summary: string;
}

// =============================================================================
// Category Colors and Labels
// =============================================================================

const CATEGORY_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  hedging: { color: 'text-amber-400', bg: 'bg-amber-500/20', label: 'Hedging' },
  clarity: { color: 'text-blue-400', bg: 'bg-blue-500/20', label: 'Clarity' },
  conciseness: { color: 'text-purple-400', bg: 'bg-purple-500/20', label: 'Conciseness' },
  tone: { color: 'text-pink-400', bg: 'bg-pink-500/20', label: 'Tone' },
  grammar: { color: 'text-red-400', bg: 'bg-red-500/20', label: 'Grammar' },
};

// =============================================================================
// Tooltip Component
// =============================================================================

interface TooltipProps {
  content: string;
  children: React.ReactNode;
}

function Tooltip({ content, children }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <span
      className="relative inline"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-[#1C1C1E] border border-white/10 rounded-lg text-xs text-white whitespace-nowrap z-50 shadow-xl"
          >
            {content}
            <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-[#1C1C1E]" />
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  );
}

// =============================================================================
// Diff Token Component
// =============================================================================

interface DiffTokenProps {
  text: string;
  type: 'unchanged' | 'removed' | 'added';
  reason?: string;
  category?: string;
}

function DiffToken({ text, type, reason, category }: DiffTokenProps) {
  if (type === 'unchanged') {
    return <span className="text-white/90">{text}</span>;
  }

  const config = category ? CATEGORY_CONFIG[category] || CATEGORY_CONFIG.clarity : CATEGORY_CONFIG.clarity;

  if (type === 'removed') {
    return (
      <Tooltip content={reason || 'Suggested removal'}>
        <span className="relative inline-block mx-0.5">
          <span className="bg-red-500/30 text-red-300 line-through decoration-red-500/70 px-1 rounded cursor-help">
            {text}
          </span>
        </span>
      </Tooltip>
    );
  }

  if (type === 'added') {
    return (
      <Tooltip content={reason || 'Suggested addition'}>
        <span className="relative inline-block mx-0.5">
          <span className="bg-green-500/30 text-green-300 px-1 rounded cursor-help">
            {text}
          </span>
        </span>
      </Tooltip>
    );
  }

  return null;
}

// =============================================================================
// Inline Diff View Component
// =============================================================================

interface InlineDiffViewProps {
  originalText: string;
  edits: StyleEdit[];
  acceptedEdits: Set<number>;
  onToggleEdit: (index: number) => void;
}

function InlineDiffView({ originalText, edits, acceptedEdits, onToggleEdit }: InlineDiffViewProps) {
  // Build the diff view by processing edits
  const diffElements = useMemo(() => {
    if (edits.length === 0) {
      return [{ type: 'unchanged' as const, text: originalText }];
    }

    // Sort edits by start index
    const sortedEdits = [...edits]
      .map((edit, idx) => ({ ...edit, idx }))
      .sort((a, b) => a.start_index - b.start_index);

    const elements: Array<{
      type: 'unchanged' | 'removed' | 'added';
      text: string;
      reason?: string;
      category?: string;
      editIndex?: number;
    }> = [];

    let currentIndex = 0;

    for (const edit of sortedEdits) {
      // Add unchanged text before this edit
      if (edit.start_index > currentIndex) {
        elements.push({
          type: 'unchanged',
          text: originalText.slice(currentIndex, edit.start_index),
        });
      }

      const isAccepted = acceptedEdits.has(edit.idx);

      if (isAccepted) {
        // Show only the suggested text (green)
        elements.push({
          type: 'added',
          text: edit.suggested,
          reason: edit.reason,
          category: edit.category,
          editIndex: edit.idx,
        });
      } else {
        // Show both removed and added
        elements.push({
          type: 'removed',
          text: edit.original,
          reason: edit.reason,
          category: edit.category,
          editIndex: edit.idx,
        });
        elements.push({
          type: 'added',
          text: edit.suggested,
          reason: edit.reason,
          category: edit.category,
          editIndex: edit.idx,
        });
      }

      currentIndex = edit.end_index;
    }

    // Add remaining unchanged text
    if (currentIndex < originalText.length) {
      elements.push({
        type: 'unchanged',
        text: originalText.slice(currentIndex),
      });
    }

    return elements;
  }, [originalText, edits, acceptedEdits]);

  return (
    <div className="font-mono text-sm leading-relaxed p-4 bg-black/30 rounded-xl border border-white/5">
      {diffElements.map((element, idx) => (
        <DiffToken
          key={idx}
          text={element.text}
          type={element.type}
          reason={element.reason}
          category={element.category}
        />
      ))}
    </div>
  );
}

// =============================================================================
// Edit Card Component
// =============================================================================

interface EditCardProps {
  edit: StyleEdit;
  index: number;
  isAccepted: boolean;
  onToggle: () => void;
}

function EditCard({ edit, index, isAccepted, onToggle }: EditCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const config = CATEGORY_CONFIG[edit.category] || CATEGORY_CONFIG.clarity;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`rounded-xl border overflow-hidden transition-all ${
        isAccepted
          ? 'border-green-500/30 bg-green-500/5'
          : 'border-white/10 bg-white/5'
      }`}
    >
      <div className="p-3 flex items-center gap-3">
        {/* Accept/Reject Toggle */}
        <button
          onClick={onToggle}
          className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
            isAccepted
              ? 'bg-green-500 text-white'
              : 'bg-white/10 text-white/50 hover:bg-white/20'
          }`}
        >
          {isAccepted ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
        </button>

        {/* Edit Preview */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
              {config.label}
            </span>
          </div>
          <div className="text-sm truncate">
            <span className="text-red-400 line-through">{edit.original}</span>
            <span className="text-white/30 mx-2">→</span>
            <span className="text-green-400">{edit.suggested}</span>
          </div>
        </div>

        {/* Expand Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex-shrink-0 p-2 hover:bg-white/10 rounded-lg transition-colors"
        >
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-white/50" />
          ) : (
            <ChevronDown className="w-4 h-4 text-white/50" />
          )}
        </button>
      </div>

      {/* Expanded Reason */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 pt-0">
              <div className="bg-black/30 rounded-lg p-3 border border-white/5">
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-[#8A8F98] flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-[#8A8F98]">{edit.reason}</p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function DNAModule() {
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState<DNAStyleResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [acceptedEdits, setAcceptedEdits] = useState<Set<number>>(new Set());
  const [copied, setCopied] = useState(false);

  const handleAnalyze = useCallback(async () => {
    if (!inputText.trim() || inputText.length < 20) return;

    setIsProcessing(true);
    setError(null);
    setResult(null);
    setAcceptedEdits(new Set());

    try {
      const res = await fetch(`${API_URL}/dna/suggest-edits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText })
      });

      if (!res.ok) throw new Error('Analysis failed');

      const data: DNAStyleResponse = await res.json();
      setResult(data);

      // Auto-accept all edits by default
      setAcceptedEdits(new Set(data.edits.map((_, idx) => idx)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    }

    setIsProcessing(false);
  }, [inputText]);

  const toggleEdit = useCallback((index: number) => {
    setAcceptedEdits(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }, []);

  const acceptAllEdits = useCallback(() => {
    if (result) {
      setAcceptedEdits(new Set(result.edits.map((_, idx) => idx)));
    }
  }, [result]);

  const rejectAllEdits = useCallback(() => {
    setAcceptedEdits(new Set());
  }, []);

  const applyChanges = useCallback(() => {
    if (!result) return;

    // Build final text with accepted edits
    let finalText = result.original_text;

    // Sort edits by start index descending to apply from end to start
    const sortedEdits = result.edits
      .map((edit, idx) => ({ ...edit, idx }))
      .filter(edit => acceptedEdits.has(edit.idx))
      .sort((a, b) => b.start_index - a.start_index);

    for (const edit of sortedEdits) {
      finalText =
        finalText.slice(0, edit.start_index) +
        edit.suggested +
        finalText.slice(edit.end_index);
    }

    setInputText(finalText);
    setResult(null);
    setAcceptedEdits(new Set());
  }, [result, acceptedEdits]);

  const copyImprovedText = useCallback(async () => {
    if (!result) return;

    let finalText = result.original_text;
    const sortedEdits = result.edits
      .map((edit, idx) => ({ ...edit, idx }))
      .filter(edit => acceptedEdits.has(edit.idx))
      .sort((a, b) => b.start_index - a.start_index);

    for (const edit of sortedEdits) {
      finalText =
        finalText.slice(0, edit.start_index) +
        edit.suggested +
        finalText.slice(edit.end_index);
    }

    await navigator.clipboard.writeText(finalText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [result, acceptedEdits]);

  const metrics = result?.style_metrics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          DNA Editor
        </h2>
        <p className="text-[#8A8F98] mt-1">Style Analysis & Diff Editor</p>
      </div>

      {/* Input Section */}
      <div className="glass-panel p-6">
        <label className="block text-sm font-medium text-[#8A8F98] mb-3">
          Your Draft
        </label>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste your draft text here to analyze and improve (minimum 20 characters)..."
          className="w-full h-40 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-[#8A8F98]/50 focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all resize-none font-mono text-sm"
        />
        <div className="mt-3 flex items-center justify-between">
          <p className="text-xs text-[#8A8F98]">
            {inputText.length} characters • {inputText.split(/\s+/).filter(Boolean).length} words
          </p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleAnalyze}
            disabled={isProcessing || inputText.length < 20}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-500/20"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Analyze & Suggest
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass-panel p-4 border-red-500/30 bg-red-500/10"
          >
            <p className="text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {error}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Section */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Summary Card */}
            <div className="glass-panel p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-1">Analysis Summary</h3>
                  <p className="text-sm text-[#8A8F98]">{result.summary}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-400 text-sm font-medium">
                    {result.edits.length} suggestions
                  </span>
                </div>
              </div>

              {/* Style Metrics */}
              {metrics && (
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div className="bg-black/30 rounded-xl p-3 text-center border border-white/5">
                    <p className="text-2xl font-bold text-white">
                      {metrics.sentence_complexity?.average_length?.toFixed(1) || '—'}
                    </p>
                    <p className="text-xs text-[#8A8F98] mt-1">Avg Sentence Length</p>
                  </div>
                  <div className="bg-black/30 rounded-xl p-3 text-center border border-white/5">
                    <p className="text-2xl font-bold text-white">
                      {metrics.hedging?.hedging_density_per_1000_words?.toFixed(1) || '—'}
                    </p>
                    <p className="text-xs text-[#8A8F98] mt-1">Hedging Density</p>
                  </div>
                  <div className="bg-black/30 rounded-xl p-3 text-center border border-white/5">
                    <p className="text-2xl font-bold text-white">
                      {acceptedEdits.size}/{result.edits.length}
                    </p>
                    <p className="text-xs text-[#8A8F98] mt-1">Edits Accepted</p>
                  </div>
                </div>
              )}
            </div>

            {/* Diff View */}
            <div className="glass-panel p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Diff View</h3>
                <div className="flex items-center gap-4 text-xs text-[#8A8F98]">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded bg-red-500/30" />
                    <span>Removed</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded bg-green-500/30" />
                    <span>Added</span>
                  </div>
                </div>
              </div>

              <InlineDiffView
                originalText={result.original_text}
                edits={result.edits}
                acceptedEdits={acceptedEdits}
                onToggleEdit={toggleEdit}
              />

              <p className="mt-3 text-xs text-[#8A8F98]">
                Hover over highlighted text to see the reason for each suggestion
              </p>
            </div>

            {/* Edit List */}
            {result.edits.length > 0 && (
              <div className="glass-panel p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Suggestions</h3>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={acceptAllEdits}
                      className="px-3 py-1.5 text-xs font-medium text-green-400 bg-green-500/10 rounded-lg hover:bg-green-500/20 transition-colors"
                    >
                      Accept All
                    </button>
                    <button
                      onClick={rejectAllEdits}
                      className="px-3 py-1.5 text-xs font-medium text-red-400 bg-red-500/10 rounded-lg hover:bg-red-500/20 transition-colors"
                    >
                      Reject All
                    </button>
                  </div>
                </div>

                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {result.edits.map((edit, idx) => (
                    <EditCard
                      key={idx}
                      edit={edit}
                      index={idx}
                      isAccepted={acceptedEdits.has(idx)}
                      onToggle={() => toggleEdit(idx)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  setResult(null);
                  setAcceptedEdits(new Set());
                }}
                className="flex items-center gap-2 px-5 py-2.5 bg-white/10 text-white font-medium rounded-xl hover:bg-white/20 transition-all"
              >
                <RotateCcw className="w-4 h-4" />
                Reset
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={copyImprovedText}
                className="flex items-center gap-2 px-5 py-2.5 bg-white/10 text-white font-medium rounded-xl hover:bg-white/20 transition-all"
              >
                {copied ? (
                  <>
                    <CheckCheck className="w-4 h-4 text-green-400" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy Result
                  </>
                )}
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={applyChanges}
                disabled={acceptedEdits.size === 0}
                className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-green-500/20"
              >
                <Check className="w-4 h-4" />
                Apply {acceptedEdits.size} Edit{acceptedEdits.size !== 1 ? 's' : ''}
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
