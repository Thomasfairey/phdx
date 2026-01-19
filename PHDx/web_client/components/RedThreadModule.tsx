'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Link2,
  Loader2,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Target,
  FileText,
  Lightbulb,
  XCircle
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// Type Definitions
// =============================================================================

interface GraphNode {
  id: string;
  label: string;
  type: 'question' | 'argument' | 'evidence' | 'conclusion';
  chapter: string;
}

interface GraphEdge {
  source: string;
  target: string;
  label?: string;
  strength: number;
}

interface MissingLink {
  from_chapter: string;
  to_chapter: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  suggestion: string;
}

interface VisualGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface RedThreadResponse {
  continuity_score: number;
  thread_status: 'solid' | 'broken' | 'unknown';
  status: string;
  analysis: string;
  missing_links?: MissingLink[];
  visual_graph_nodes?: GraphNode[];
  visual_graph_edges?: GraphEdge[];
  chapter_abstracts?: Array<{
    chapter_id: string;
    chapter_title: string;
    core_argument: string;
  }>;
}

// =============================================================================
// Thread Node Component
// =============================================================================

interface ThreadNodeProps {
  node: {
    id: string;
    label: string;
    chapter: string;
    type: string;
  };
  index: number;
  isLast: boolean;
  nextConnectionStatus: 'solid' | 'broken' | 'none';
  missingLink?: MissingLink;
  onMissingLinkClick: (link: MissingLink) => void;
}

function ThreadNode({
  node,
  index,
  isLast,
  nextConnectionStatus,
  missingLink,
  onMissingLinkClick
}: ThreadNodeProps) {
  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'question': return <Target className="w-5 h-5" />;
      case 'conclusion': return <Lightbulb className="w-5 h-5" />;
      case 'evidence': return <FileText className="w-5 h-5" />;
      default: return <BookOpen className="w-5 h-5" />;
    }
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'question': return 'from-blue-500 to-cyan-500';
      case 'conclusion': return 'from-purple-500 to-pink-500';
      case 'evidence': return 'from-amber-500 to-orange-500';
      default: return 'from-emerald-500 to-teal-500';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="relative"
    >
      {/* Node */}
      <div className="flex items-center gap-4">
        {/* Node Circle */}
        <div className={`relative z-10 w-12 h-12 rounded-full bg-gradient-to-br ${getNodeColor(node.type)} flex items-center justify-center shadow-lg`}>
          <div className="text-white">
            {getNodeIcon(node.type)}
          </div>
          {/* Glow effect */}
          <div className={`absolute inset-0 rounded-full bg-gradient-to-br ${getNodeColor(node.type)} blur-md opacity-50`} />
        </div>

        {/* Node Content */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-[#8A8F98] uppercase tracking-wider">
              {node.chapter}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-[#8A8F98]">
              {node.type}
            </span>
          </div>
          <h4 className="text-white font-medium mt-1">{node.label}</h4>
        </div>
      </div>

      {/* Connection Line to Next Node */}
      {!isLast && (
        <div className="relative ml-6 my-2">
          {/* Thread Line */}
          <div className="absolute left-0 top-0 w-0.5 h-16">
            {nextConnectionStatus === 'solid' ? (
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: '100%' }}
                transition={{ delay: index * 0.1 + 0.2, duration: 0.3 }}
                className="w-full bg-gradient-to-b from-green-500 to-emerald-500 rounded-full"
                style={{
                  boxShadow: '0 0 10px rgba(34, 197, 94, 0.5), 0 0 20px rgba(34, 197, 94, 0.3)'
                }}
              />
            ) : nextConnectionStatus === 'broken' ? (
              <div className="w-full h-full relative">
                {/* Broken line segments */}
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: '40%' }}
                  transition={{ delay: index * 0.1 + 0.2 }}
                  className="absolute top-0 w-full bg-gradient-to-b from-red-500 to-red-600 rounded-full"
                />
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: '40%' }}
                  transition={{ delay: index * 0.1 + 0.3 }}
                  className="absolute bottom-0 w-full bg-gradient-to-b from-red-600 to-red-500 rounded-full"
                />
                {/* Gap with warning */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: index * 0.1 + 0.4, type: 'spring' }}
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
                >
                  <button
                    onClick={() => missingLink && onMissingLinkClick(missingLink)}
                    className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center hover:bg-red-400 transition-colors cursor-pointer group"
                    title="Click to see details"
                  >
                    <AlertTriangle className="w-3.5 h-3.5 text-white" />
                    <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-50" />
                  </button>
                </motion.div>
              </div>
            ) : (
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: '100%' }}
                transition={{ delay: index * 0.1 + 0.2 }}
                className="w-full bg-white/10 rounded-full"
              />
            )}
          </div>
        </div>
      )}
    </motion.div>
  );
}

// =============================================================================
// Missing Link Card Component
// =============================================================================

interface MissingLinkCardProps {
  link: MissingLink;
  isExpanded: boolean;
  onToggle: () => void;
}

function MissingLinkCard({ link, isExpanded, onToggle }: MissingLinkCardProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'border-red-500/50 bg-red-500/10';
      case 'medium': return 'border-amber-500/50 bg-amber-500/10';
      case 'low': return 'border-yellow-500/50 bg-yellow-500/10';
      default: return 'border-white/10 bg-white/5';
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-500/20 text-red-400';
      case 'medium': return 'bg-amber-500/20 text-amber-400';
      case 'low': return 'bg-yellow-500/20 text-yellow-400';
      default: return 'bg-white/10 text-white/60';
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl border ${getSeverityColor(link.severity)} overflow-hidden`}
    >
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <XCircle className="w-5 h-5 text-red-400" />
          <span className="text-white font-medium">
            {link.from_chapter} → {link.to_chapter}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getSeverityBadge(link.severity)}`}>
            {link.severity}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-[#8A8F98]" />
        ) : (
          <ChevronDown className="w-5 h-5 text-[#8A8F98]" />
        )}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3">
              <div>
                <h5 className="text-xs font-medium text-[#8A8F98] uppercase tracking-wider mb-1">
                  Issue
                </h5>
                <p className="text-white text-sm">{link.description}</p>
              </div>
              <div>
                <h5 className="text-xs font-medium text-[#8A8F98] uppercase tracking-wider mb-1">
                  Suggestion
                </h5>
                <p className="text-emerald-400 text-sm">{link.suggestion}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// =============================================================================
// Golden Thread Visualization
// =============================================================================

interface GoldenThreadProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  missingLinks: MissingLink[];
  threadStatus: 'solid' | 'broken' | 'unknown';
}

function GoldenThread({ nodes, edges, missingLinks, threadStatus }: GoldenThreadProps) {
  const [expandedLink, setExpandedLink] = useState<string | null>(null);
  const [selectedMissingLink, setSelectedMissingLink] = useState<MissingLink | null>(null);

  // Create a simple chapter-based node list if no nodes provided
  const displayNodes = nodes.length > 0 ? nodes : [
    { id: 'ch1', label: 'Research Question', type: 'question' as const, chapter: 'Chapter 1' },
    { id: 'ch2', label: 'Literature Review', type: 'argument' as const, chapter: 'Chapter 2' },
    { id: 'ch3', label: 'Methodology', type: 'evidence' as const, chapter: 'Chapter 3' },
    { id: 'ch4', label: 'Results', type: 'evidence' as const, chapter: 'Chapter 4' },
    { id: 'ch5', label: 'Conclusion', type: 'conclusion' as const, chapter: 'Chapter 5' },
  ];

  // Determine connection status between nodes
  const getConnectionStatus = (fromId: string, toId: string): 'solid' | 'broken' | 'none' => {
    // Check if there's a missing link between these chapters
    const fromChapter = fromId.replace('ch', 'Chapter ').replace('_', ' ');
    const toChapter = toId.replace('ch', 'Chapter ').replace('_', ' ');

    const hasMissingLink = missingLinks.some(
      link => link.from_chapter.includes(fromId) || link.to_chapter.includes(toId) ||
              link.from_chapter.toLowerCase().includes(fromChapter.toLowerCase()) ||
              link.to_chapter.toLowerCase().includes(toChapter.toLowerCase())
    );

    if (hasMissingLink) return 'broken';
    if (threadStatus === 'solid') return 'solid';
    if (threadStatus === 'broken' && missingLinks.length === 0) return 'broken';
    return 'solid';
  };

  const handleMissingLinkClick = (link: MissingLink) => {
    setSelectedMissingLink(link);
    setExpandedLink(link.from_chapter + link.to_chapter);
  };

  return (
    <div className="space-y-6">
      {/* Thread Visualization */}
      <div className="glass-panel p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className={`w-3 h-3 rounded-full ${threadStatus === 'solid' ? 'bg-green-500' : 'bg-red-500'}`} />
          <h3 className="text-lg font-semibold text-white">
            Argument Flow {threadStatus === 'solid' ? '(Connected)' : '(Broken Links Detected)'}
          </h3>
        </div>

        <div className="relative pl-4">
          {displayNodes.map((node, index) => {
            const nextNode = displayNodes[index + 1];
            const connectionStatus = nextNode
              ? getConnectionStatus(node.id, nextNode.id)
              : 'none';

            // Find relevant missing link
            const relevantMissingLink = missingLinks.find(
              link => link.from_chapter.toLowerCase().includes(node.chapter.toLowerCase().replace('chapter ', 'ch'))
            );

            return (
              <ThreadNode
                key={node.id}
                node={node}
                index={index}
                isLast={index === displayNodes.length - 1}
                nextConnectionStatus={connectionStatus}
                missingLink={relevantMissingLink}
                onMissingLinkClick={handleMissingLinkClick}
              />
            );
          })}
        </div>
      </div>

      {/* Missing Links Details */}
      {missingLinks.length > 0 && (
        <div className="glass-panel p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            Missing Links ({missingLinks.length})
          </h3>
          <div className="space-y-3">
            {missingLinks.map((link, index) => (
              <MissingLinkCard
                key={index}
                link={link}
                isExpanded={expandedLink === link.from_chapter + link.to_chapter}
                onToggle={() => setExpandedLink(
                  expandedLink === link.from_chapter + link.to_chapter
                    ? null
                    : link.from_chapter + link.to_chapter
                )}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function RedThreadModule() {
  const [introduction, setIntroduction] = useState('');
  const [discussion, setDiscussion] = useState('');
  const [result, setResult] = useState<RedThreadResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCheck = useCallback(async () => {
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
  }, [introduction, discussion]);

  const getScoreColor = (score: number) => {
    if (score < 30) return { bg: 'bg-red-500', text: 'text-red-400', ring: 'ring-red-500/30', glow: 'shadow-red-500/30' };
    if (score < 70) return { bg: 'bg-amber-500', text: 'text-amber-400', ring: 'ring-amber-500/30', glow: 'shadow-amber-500/30' };
    return { bg: 'bg-green-500', text: 'text-green-400', ring: 'ring-green-500/30', glow: 'shadow-green-500/30' };
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
            Introduction / Chapter 1
          </label>
          <textarea
            value={introduction}
            onChange={(e) => setIntroduction(e.target.value)}
            placeholder="Paste your introduction section here..."
            className="w-full h-48 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-[#8A8F98]/50 focus:border-red-500/50 focus:ring-2 focus:ring-red-500/20 transition-all resize-none"
          />
          <p className="mt-2 text-xs text-[#8A8F98]">
            {introduction.length} characters • {introduction.split(/\s+/).filter(Boolean).length} words
          </p>
        </div>

        {/* Discussion */}
        <div className="glass-panel p-6">
          <label className="block text-sm font-medium text-[#8A8F98] mb-3">
            Discussion / Conclusion
          </label>
          <textarea
            value={discussion}
            onChange={(e) => setDiscussion(e.target.value)}
            placeholder="Paste your discussion/conclusion section here..."
            className="w-full h-48 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-[#8A8F98]/50 focus:border-orange-500/50 focus:ring-2 focus:ring-orange-500/20 transition-all resize-none"
          />
          <p className="mt-2 text-xs text-[#8A8F98]">
            {discussion.length} characters • {discussion.split(/\s+/).filter(Boolean).length} words
          </p>
        </div>
      </div>

      {/* Action Button */}
      <div className="flex justify-center">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleCheck}
          disabled={isProcessing || !introduction.trim() || !discussion.trim()}
          className="flex items-center gap-3 px-8 py-3 bg-gradient-to-r from-red-500 to-orange-600 text-white font-medium rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-lg shadow-red-500/20"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing Argument Flow...
            </>
          ) : (
            <>
              <Link2 className="w-5 h-5" />
              Check Continuity
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </motion.button>
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
              <AlertTriangle className="w-4 h-4" />
              {error}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Section */}
      <AnimatePresence>
        {result && scoreColors && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Score and Status Card */}
            <div className="glass-panel p-6">
              <div className="flex items-start gap-8">
                {/* Score Circle */}
                <div className="flex-shrink-0">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', delay: 0.2 }}
                    className={`relative w-32 h-32 rounded-full ring-4 ${scoreColors.ring} flex items-center justify-center shadow-lg ${scoreColors.glow}`}
                  >
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
                      <motion.circle
                        initial={{ strokeDasharray: '0 352' }}
                        animate={{ strokeDasharray: `${result.continuity_score * 3.52} 352` }}
                        transition={{ duration: 1, delay: 0.3 }}
                        cx="64"
                        cy="64"
                        r="56"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        className={scoreColors.text}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="text-center">
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        className={`text-4xl font-bold ${scoreColors.text}`}
                      >
                        {Math.round(result.continuity_score)}
                      </motion.span>
                      <span className={`text-lg ${scoreColors.text}`}>%</span>
                    </div>
                  </motion.div>
                  <p className="text-center text-sm text-[#8A8F98] mt-3">Continuity Score</p>
                </div>

                {/* Status and Analysis */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-4">
                    {result.thread_status === 'solid' ? (
                      <CheckCircle2 className="w-6 h-6 text-green-400" />
                    ) : (
                      <AlertTriangle className="w-6 h-6 text-red-400" />
                    )}
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      result.continuity_score < 30
                        ? 'bg-red-500/20 text-red-400'
                        : result.continuity_score < 70
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-green-500/20 text-green-400'
                    }`}>
                      {result.status}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      result.thread_status === 'solid'
                        ? 'bg-green-500/10 text-green-400'
                        : 'bg-red-500/10 text-red-400'
                    }`}>
                      Thread: {result.thread_status}
                    </span>
                  </div>

                  <h3 className="text-sm font-medium text-[#8A8F98] mb-2">Analysis Summary</h3>
                  <div className="bg-black/30 rounded-xl p-4 border border-white/5">
                    <p className="text-white leading-relaxed text-sm">{result.analysis}</p>
                  </div>

                  {/* Score Legend */}
                  <div className="mt-4 flex items-center gap-6 text-xs text-[#8A8F98]">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-red-500" />
                      <span>Broken (&lt;30%)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-amber-500" />
                      <span>Weak (30-70%)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-green-500" />
                      <span>Strong (&gt;70%)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Golden Thread Visualization */}
            <GoldenThread
              nodes={result.visual_graph_nodes || []}
              edges={result.visual_graph_edges || []}
              missingLinks={result.missing_links || []}
              threadStatus={result.thread_status || 'unknown'}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
