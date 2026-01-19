'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Swords,
  Send,
  Volume2,
  VolumeX,
  Upload,
  CloudDownload,
  StopCircle,
  Loader2,
  AlertTriangle,
  CheckCircle,
  XCircle,
  BarChart3,
  Skull,
  Shield,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

type MessageRole = 'examiner' | 'candidate' | 'system';
type Rating = 'WEAK' | 'EVASIVE' | 'ADEQUATE' | 'STRONG';

interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  rating?: Rating;
  feedback?: string;
  questionNumber?: number;
}

interface SessionSummary {
  total_questions: number;
  total_answers: number;
  rating_breakdown: Record<string, number>;
  average_score: number;
  verdict: string;
  verdict_detail: string;
}

// =============================================================================
// Rating Badge Component
// =============================================================================

const ratingConfig: Record<Rating, { color: string; bgColor: string; icon: typeof CheckCircle }> = {
  STRONG: { color: 'text-green-400', bgColor: 'bg-green-500/20', icon: CheckCircle },
  ADEQUATE: { color: 'text-blue-400', bgColor: 'bg-blue-500/20', icon: Shield },
  EVASIVE: { color: 'text-yellow-400', bgColor: 'bg-yellow-500/20', icon: AlertTriangle },
  WEAK: { color: 'text-red-400', bgColor: 'bg-red-500/20', icon: XCircle },
};

function RatingBadge({ rating }: { rating: Rating }) {
  const config = ratingConfig[rating];
  const Icon = config.icon;

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded ${config.bgColor} ${config.color} text-xs font-mono`}>
      <Icon className="w-3 h-3" />
      {rating}
    </div>
  );
}

// =============================================================================
// Message Component
// =============================================================================

function ChatMessage({ message, isTyping }: { message: Message; isTyping?: boolean }) {
  const isExaminer = message.role === 'examiner';
  const isSystem = message.role === 'system';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`mb-4 ${isSystem ? 'px-4' : ''}`}
    >
      {isSystem ? (
        // System message
        <div className="text-center py-2">
          <span className="text-xs text-[#8A8F98] font-mono bg-white/5 px-3 py-1 rounded">
            {message.content}
          </span>
        </div>
      ) : (
        <div className={`flex ${isExaminer ? 'justify-start' : 'justify-end'}`}>
          <div className={`max-w-[80%] ${isExaminer ? 'order-2' : 'order-1'}`}>
            {/* Header */}
            <div className={`flex items-center gap-2 mb-1 ${isExaminer ? '' : 'justify-end'}`}>
              {isExaminer && (
                <div className="w-6 h-6 rounded bg-red-500/20 flex items-center justify-center">
                  <Skull className="w-3 h-3 text-red-400" />
                </div>
              )}
              <span className={`text-xs font-mono ${isExaminer ? 'text-red-400' : 'text-cyan-400'}`}>
                {isExaminer ? 'EXAMINER' : 'YOU'}
              </span>
              {message.questionNumber && (
                <span className="text-xs text-[#8A8F98] font-mono">
                  Q{message.questionNumber}
                </span>
              )}
              <span className="text-xs text-[#8A8F98]">
                {message.timestamp.toLocaleTimeString()}
              </span>
            </div>

            {/* Rating badge for examiner messages */}
            {isExaminer && message.rating && (
              <div className="mb-2">
                <RatingBadge rating={message.rating} />
                {message.feedback && (
                  <p className="text-xs text-[#8A8F98] mt-1 font-mono">{message.feedback}</p>
                )}
              </div>
            )}

            {/* Message bubble */}
            <div
              className={`
                p-4 rounded-lg font-mono text-sm leading-relaxed
                ${isExaminer
                  ? 'bg-red-950/40 border border-red-500/20 text-red-100'
                  : 'bg-cyan-950/40 border border-cyan-500/20 text-cyan-100'
                }
                ${isTyping ? 'animate-pulse' : ''}
              `}
            >
              {message.content}
              {isTyping && (
                <span className="inline-block w-2 h-4 bg-current ml-1 animate-pulse" />
              )}
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// =============================================================================
// Summary Panel
// =============================================================================

function SummaryPanel({ summary, onClose }: { summary: SessionSummary; onClose: () => void }) {
  const getVerdictColor = () => {
    if (summary.verdict.includes('PASS -')) return 'text-green-400';
    if (summary.verdict.includes('MINOR')) return 'text-yellow-400';
    if (summary.verdict.includes('MAJOR')) return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="absolute inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50"
    >
      <div className="bg-[#0a0a0a] border border-white/10 rounded-xl p-8 max-w-lg w-full mx-4">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-lg bg-red-500/20 flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-red-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Defense Complete</h2>
            <p className="text-sm text-[#8A8F98]">Examination Summary</p>
          </div>
        </div>

        {/* Verdict */}
        <div className="mb-6 p-4 rounded-lg bg-white/5 border border-white/10">
          <p className={`text-lg font-bold font-mono ${getVerdictColor()}`}>
            {summary.verdict}
          </p>
          <p className="text-sm text-[#8A8F98] mt-2">{summary.verdict_detail}</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="p-3 rounded-lg bg-white/5">
            <p className="text-xs text-[#8A8F98] uppercase tracking-wider">Questions</p>
            <p className="text-2xl font-bold text-white">{summary.total_questions}</p>
          </div>
          <div className="p-3 rounded-lg bg-white/5">
            <p className="text-xs text-[#8A8F98] uppercase tracking-wider">Avg Score</p>
            <p className="text-2xl font-bold text-white">{summary.average_score}%</p>
          </div>
        </div>

        {/* Rating breakdown */}
        <div className="mb-6">
          <p className="text-sm text-[#8A8F98] mb-2">Response Quality</p>
          <div className="flex gap-2">
            {Object.entries(summary.rating_breakdown).map(([rating, count]) => (
              <div key={rating} className="flex-1 text-center p-2 rounded bg-white/5">
                <p className={`text-lg font-bold ${ratingConfig[rating as Rating]?.color || 'text-white'}`}>
                  {count}
                </p>
                <p className="text-xs text-[#8A8F98]">{rating}</p>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full py-3 rounded-lg bg-white/10 hover:bg-white/20 transition-colors text-white font-medium"
        >
          Close
        </button>
      </div>
    </motion.div>
  );
}

// =============================================================================
// Main War Room Module
// =============================================================================

export function WarRoomModule() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionActive, setSessionActive] = useState(false);
  const [thesisText, setThesisText] = useState('');
  const [showUpload, setShowUpload] = useState(true);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const userId = 'default'; // In production, use actual user ID

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Text-to-speech for examiner messages
  const speakText = useCallback((text: string) => {
    if (!voiceEnabled || typeof window === 'undefined') return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 0.8;
    utterance.volume = 1;

    // Try to use a serious voice
    const voices = speechSynthesis.getVoices();
    const seriousVoice = voices.find(v =>
      v.name.includes('Daniel') || v.name.includes('Alex') || v.lang.startsWith('en-GB')
    );
    if (seriousVoice) utterance.voice = seriousVoice;

    speechSynthesis.speak(utterance);
  }, [voiceEnabled]);

  // Add examiner message with optional TTS
  const addExaminerMessage = useCallback((content: string, rating?: Rating, feedback?: string, questionNumber?: number) => {
    const msg: Message = {
      id: Date.now().toString(),
      role: 'examiner',
      content,
      timestamp: new Date(),
      rating,
      feedback,
      questionNumber,
    };
    setMessages(prev => [...prev, msg]);

    // Speak the question
    if (voiceEnabled) {
      speakText(content);
    }
  }, [voiceEnabled, speakText]);

  // Start defense session
  const startDefense = async () => {
    if (!thesisText.trim() || thesisText.length < 500) {
      setError('Please provide at least 500 characters of thesis text.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/war-room/start?user_id=${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ thesis_text: thesisText }),
        }
      );

      const data = await response.json();

      if (data.success && data.question) {
        setShowUpload(false);
        setSessionActive(true);
        setMessages([
          {
            id: 'system-1',
            role: 'system',
            content: 'VIVA VOCE EXAMINATION COMMENCED',
            timestamp: new Date(),
          },
        ]);
        addExaminerMessage(data.question, undefined, undefined, data.question_number);
      } else {
        setError(data.error || 'Failed to start defense');
      }
    } catch (err) {
      setError('Connection failed. Is the server running?');
    } finally {
      setIsLoading(false);
    }
  };

  // Load from Google Drive
  const loadFromDrive = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/war-room/load-from-drive?user_id=${userId}`,
        { method: 'POST' }
      );

      const data = await response.json();

      if (data.success) {
        setShowUpload(false);
        setSessionActive(true);
        setMessages([
          {
            id: 'system-1',
            role: 'system',
            content: `LOADED ${data.chapters_loaded.length} CHAPTERS (${data.word_count.toLocaleString()} WORDS)`,
            timestamp: new Date(),
          },
        ]);

        // Now start the defense
        const startResponse = await fetch(
          `http://localhost:8000/api/war-room/start?user_id=${userId}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ thesis_text: 'LOADED_FROM_DRIVE' }),
          }
        );
        // Note: The thesis was already loaded via load-from-drive
        // We just need to call start_defense which will use the already loaded context
      } else {
        setError(data.detail || data.error || 'Failed to load from Drive');
      }
    } catch (err) {
      setError('Failed to connect to Drive. Please authenticate first.');
    } finally {
      setIsLoading(false);
    }
  };

  // Submit answer
  const submitAnswer = async () => {
    if (!inputText.trim() || isLoading) return;

    const answer = inputText.trim();
    setInputText('');
    setIsLoading(true);

    // Add candidate message
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'candidate',
      content: answer,
      timestamp: new Date(),
    }]);

    try {
      const response = await fetch(
        `http://localhost:8000/api/war-room/answer?user_id=${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answer }),
        }
      );

      const data = await response.json();

      if (data.success && data.next_question) {
        addExaminerMessage(
          data.next_question,
          data.rating,
          data.feedback,
          data.question_number
        );
      } else if (data.error) {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to submit answer');
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  // End defense
  const endDefense = async () => {
    setIsLoading(true);

    try {
      const response = await fetch(
        `http://localhost:8000/api/war-room/end?user_id=${userId}`,
        { method: 'POST' }
      );

      const data = await response.json();

      if (data.success && data.summary) {
        setSummary(data.summary);
        setSessionActive(false);
        setMessages(prev => [...prev, {
          id: 'system-end',
          role: 'system',
          content: 'EXAMINATION CONCLUDED',
          timestamp: new Date(),
        }]);
      }
    } catch (err) {
      setError('Failed to end session');
    } finally {
      setIsLoading(false);
    }
  };

  // Reset session
  const resetSession = () => {
    setMessages([]);
    setShowUpload(true);
    setSessionActive(false);
    setSummary(null);
    setThesisText('');
    setError(null);
  };

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitAnswer();
    }
  };

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-red-600 to-red-800 flex items-center justify-center">
            <Swords className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">War Room</h1>
            <p className="text-sm text-[#8A8F98]">Viva Voce Examination Simulator</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Voice toggle */}
          <button
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            className={`p-2 rounded-lg transition-colors ${
              voiceEnabled ? 'bg-red-500/20 text-red-400' : 'bg-white/5 text-[#8A8F98]'
            }`}
            title={voiceEnabled ? 'Disable voice' : 'Enable voice'}
          >
            {voiceEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>

          {sessionActive && (
            <button
              onClick={endDefense}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
            >
              <StopCircle className="w-4 h-4" />
              End Defense
            </button>
          )}
        </div>
      </div>

      {/* Error banner */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2"
          >
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span className="text-sm text-red-400">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-300"
            >
              <XCircle className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main content */}
      {showUpload ? (
        // Upload/Load screen
        <div className="flex-1 flex items-center justify-center">
          <div className="max-w-2xl w-full space-y-6">
            <div className="text-center mb-8">
              <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
                <Skull className="w-10 h-10 text-red-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Prepare for Examination</h2>
              <p className="text-[#8A8F98]">
                Load your thesis and face a hostile examiner. They will probe for weaknesses
                and challenge your methodology. No mercy will be shown.
              </p>
            </div>

            {/* Thesis input */}
            <div className="glass-panel rounded-xl p-4">
              <label className="block text-sm text-[#8A8F98] mb-2 font-mono">
                PASTE THESIS TEXT (MIN 500 CHARS)
              </label>
              <textarea
                value={thesisText}
                onChange={(e) => setThesisText(e.target.value)}
                placeholder="Paste your introduction, methodology, results, and discussion sections here..."
                className="w-full h-48 bg-black/40 border border-white/10 rounded-lg p-4 text-white text-sm font-mono resize-none focus:outline-none focus:border-red-500/50"
              />
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-[#8A8F98]">
                  {thesisText.length} characters ({Math.round(thesisText.length / 5)} words)
                </span>
                <button
                  onClick={startDefense}
                  disabled={isLoading || thesisText.length < 500}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-white font-medium"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Upload className="w-4 h-4" />
                  )}
                  Begin Examination
                </button>
              </div>
            </div>

            {/* Or load from Drive */}
            <div className="flex items-center gap-4">
              <div className="flex-1 h-px bg-white/10" />
              <span className="text-xs text-[#8A8F98] uppercase tracking-wider">Or</span>
              <div className="flex-1 h-px bg-white/10" />
            </div>

            <button
              onClick={loadFromDrive}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-50 transition-colors text-white"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CloudDownload className="w-4 h-4" />
              )}
              Load from Google Drive
            </button>
          </div>
        </div>
      ) : (
        // Chat interface
        <div className="flex-1 flex flex-col glass-panel rounded-xl overflow-hidden">
          {/* Terminal header */}
          <div className="px-4 py-2 bg-red-950/40 border-b border-red-500/20 flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <div className="w-3 h-3 rounded-full bg-green-500" />
            </div>
            <span className="text-xs font-mono text-red-400 ml-2">
              VIVA_VOCE_TERMINAL — EXAMINATION IN PROGRESS
            </span>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 bg-black/40">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-[#8A8F98] text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="font-mono">Examiner is thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="p-4 border-t border-white/10 bg-black/60">
            <div className="flex gap-2">
              <textarea
                ref={inputRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your response... (Enter to send, Shift+Enter for new line)"
                disabled={isLoading || !sessionActive}
                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white text-sm font-mono resize-none focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
                rows={2}
              />
              <button
                onClick={submitAnswer}
                disabled={isLoading || !inputText.trim() || !sessionActive}
                className="px-4 rounded-lg bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <Send className="w-5 h-5 text-white" />
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Summary overlay */}
      {summary && (
        <SummaryPanel summary={summary} onClose={resetSession} />
      )}
    </div>
  );
}

export default WarRoomModule;
