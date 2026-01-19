'use client';

import { useCallback, useEffect, useState, useMemo } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Position,
  Handle,
  NodeProps,
  EdgeProps,
  getBezierPath,
  BaseEdge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw,
  Loader2,
  Link2,
  Eye,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

export type ChapterStatus = 'draft' | 'reviewing' | 'solid' | 'issues';

export interface ChapterNode {
  id: string;
  name: string;
  docId?: string;
  status: ChapterStatus;
  lastSynced?: string;
  logicErrors: number;
  wordCount?: number;
  webViewLink?: string;
}

export interface LogicEdge {
  source: string;
  target: string;
  status: 'solid' | 'broken';
  errorDescription?: string;
  severity?: 'high' | 'medium' | 'low';
}

export interface ThesisGraphData {
  chapters: ChapterNode[];
  connections: LogicEdge[];
  lastAnalyzed?: string;
  overallScore?: number;
}

// =============================================================================
// Status Configuration
// =============================================================================

const statusConfig: Record<ChapterStatus, {
  color: string;
  bgGradient: string;
  borderColor: string;
  glowColor: string;
  label: string;
  Icon: typeof FileText;
}> = {
  draft: {
    color: '#8A8F98',
    bgGradient: 'from-gray-600/20 to-gray-700/20',
    borderColor: 'border-gray-500/30',
    glowColor: 'shadow-gray-500/20',
    label: 'Draft',
    Icon: FileText,
  },
  reviewing: {
    color: '#007AFF',
    bgGradient: 'from-blue-500/20 to-blue-600/20',
    borderColor: 'border-blue-500/30',
    glowColor: 'shadow-blue-500/30',
    label: 'Reviewing',
    Icon: Eye,
  },
  solid: {
    color: '#30D158',
    bgGradient: 'from-green-500/20 to-emerald-600/20',
    borderColor: 'border-green-500/30',
    glowColor: 'shadow-green-500/30',
    label: 'Solid',
    Icon: CheckCircle,
  },
  issues: {
    color: '#FF453A',
    bgGradient: 'from-red-500/20 to-orange-600/20',
    borderColor: 'border-red-500/30',
    glowColor: 'shadow-red-500/30',
    label: 'Issues Found',
    Icon: AlertTriangle,
  },
};

// =============================================================================
// Custom Chapter Node
// =============================================================================

interface ChapterNodeData {
  name: string;
  status: ChapterStatus;
  lastSynced?: string;
  logicErrors: number;
  wordCount?: number;
  webViewLink?: string;
  onNodeClick?: (id: string) => void;
}

function ChapterNodeComponent({ id, data }: NodeProps<Node<ChapterNodeData>>) {
  const [isHovered, setIsHovered] = useState(false);
  const config = statusConfig[data.status];
  const Icon = config.Icon;

  const formatLastSynced = (isoString?: string) => {
    if (!isoString) return 'Never synced';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  return (
    <div
      className="relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Input Handle (left) */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-3 !h-3 !bg-white/20 !border-2 !border-white/40"
      />

      {/* Node Body */}
      <motion.div
        className={`
          relative min-w-[180px] rounded-xl border backdrop-blur-md
          bg-gradient-to-br ${config.bgGradient} ${config.borderColor}
          transition-all duration-300 cursor-pointer
          ${isHovered ? `shadow-lg ${config.glowColor}` : ''}
        `}
        whileHover={{ scale: 1.02 }}
        onClick={() => data.onNodeClick?.(id)}
      >
        {/* Header */}
        <div className="flex items-center gap-2 p-3 border-b border-white/5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${config.color}20` }}
          >
            <Icon className="w-4 h-4" style={{ color: config.color }} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{data.name}</p>
            <p className="text-xs" style={{ color: config.color }}>
              {config.label}
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="p-3 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#8A8F98]">Last synced</span>
            <span className="text-white/70">{formatLastSynced(data.lastSynced)}</span>
          </div>
          {data.logicErrors > 0 && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#8A8F98]">Logic Errors</span>
              <span className="text-red-400 font-medium">{data.logicErrors}</span>
            </div>
          )}
          {data.wordCount && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#8A8F98]">Words</span>
              <span className="text-white/70">{data.wordCount.toLocaleString()}</span>
            </div>
          )}
        </div>

        {/* Status Indicator */}
        <div
          className="absolute -top-1 -right-1 w-3 h-3 rounded-full animate-pulse"
          style={{ backgroundColor: config.color }}
        />
      </motion.div>

      {/* Hover Tooltip */}
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute -bottom-16 left-1/2 -translate-x-1/2 z-50 min-w-[200px]"
          >
            <div className="glass-panel rounded-lg p-3 text-xs">
              <div className="flex items-center gap-2 text-white">
                <Clock className="w-3 h-3 text-[#8A8F98]" />
                <span>Last synced: {formatLastSynced(data.lastSynced)}</span>
              </div>
              {data.logicErrors > 0 && (
                <div className="flex items-center gap-2 text-red-400 mt-1">
                  <AlertTriangle className="w-3 h-3" />
                  <span>{data.logicErrors} Logic Error{data.logicErrors > 1 ? 's' : ''} found</span>
                </div>
              )}
              {data.logicErrors === 0 && (
                <div className="flex items-center gap-2 text-green-400 mt-1">
                  <CheckCircle className="w-3 h-3" />
                  <span>No issues detected</span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Output Handle (right) */}
      <Handle
        type="source"
        position={Position.Right}
        className="!w-3 !h-3 !bg-white/20 !border-2 !border-white/40"
      />
    </div>
  );
}

// =============================================================================
// Custom Edge with Animation
// =============================================================================

interface LogicEdgeData {
  status: 'solid' | 'broken';
  errorDescription?: string;
}

function LogicEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
}: EdgeProps<Edge<LogicEdgeData>>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const isBroken = data?.status === 'broken';

  return (
    <>
      {/* Glow effect for broken edges */}
      {isBroken && (
        <path
          d={edgePath}
          fill="none"
          stroke="#FF453A"
          strokeWidth={8}
          strokeOpacity={0.2}
          className="animate-pulse"
        />
      )}

      {/* Main edge */}
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke: isBroken ? '#FF453A' : '#30D158',
          strokeWidth: isBroken ? 3 : 2,
          strokeDasharray: isBroken ? '8 4' : undefined,
        }}
      />

      {/* Animated particles for solid connections */}
      {!isBroken && (
        <circle r="3" fill="#30D158" filter="url(#glow)">
          <animateMotion dur="3s" repeatCount="indefinite" path={edgePath} />
        </circle>
      )}

      {/* Broken edge label */}
      {isBroken && (
        <foreignObject
          x={labelX - 12}
          y={labelY - 12}
          width={24}
          height={24}
          className="overflow-visible"
        >
          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-red-500 animate-pulse">
            <AlertTriangle className="w-3 h-3 text-white" />
          </div>
        </foreignObject>
      )}
    </>
  );
}

// =============================================================================
// Node and Edge Types
// =============================================================================

const nodeTypes = {
  chapter: ChapterNodeComponent,
};

const edgeTypes = {
  logic: LogicEdgeComponent,
};

// =============================================================================
// Main ThesisGraph Component
// =============================================================================

interface ThesisGraphProps {
  userId?: string;
  onNodeSelect?: (chapterId: string) => void;
}

export function ThesisGraph({ userId = 'default', onNodeSelect }: ThesisGraphProps) {
  const [graphData, setGraphData] = useState<ThesisGraphData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Fetch graph data from API
  const fetchGraphData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/project/graph?user_id=${userId}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch graph: ${response.statusText}`);
      }

      const data: ThesisGraphData = await response.json();
      setGraphData(data);
    } catch (err) {
      console.error('Graph fetch error:', err);
      setError(err instanceof Error ? err.message : 'Failed to load thesis graph');
      // Use demo data on error
      setGraphData(getDemoData());
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  // Convert graph data to ReactFlow nodes/edges
  useEffect(() => {
    if (!graphData) return;

    // Create nodes with auto-layout
    const flowNodes: Node<ChapterNodeData>[] = graphData.chapters.map((chapter, index) => ({
      id: chapter.id,
      type: 'chapter',
      position: {
        x: 50 + index * 280,
        y: 150 + (index % 2) * 80, // Slight vertical offset for visual interest
      },
      data: {
        name: chapter.name,
        status: chapter.status,
        lastSynced: chapter.lastSynced,
        logicErrors: chapter.logicErrors,
        wordCount: chapter.wordCount,
        webViewLink: chapter.webViewLink,
        onNodeClick: onNodeSelect,
      },
    }));

    // Create edges
    const flowEdges: Edge<LogicEdgeData>[] = graphData.connections.map((conn, index) => ({
      id: `edge-${index}`,
      source: conn.source,
      target: conn.target,
      type: 'logic',
      animated: conn.status === 'solid',
      data: {
        status: conn.status,
        errorDescription: conn.errorDescription,
      },
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [graphData, onNodeSelect, setNodes, setEdges]);

  // Initial fetch
  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  // Calculate stats
  const stats = useMemo(() => {
    if (!graphData) return null;

    const totalChapters = graphData.chapters.length;
    const solidChapters = graphData.chapters.filter(c => c.status === 'solid').length;
    const issueChapters = graphData.chapters.filter(c => c.status === 'issues').length;
    const brokenConnections = graphData.connections.filter(c => c.status === 'broken').length;
    const totalLogicErrors = graphData.chapters.reduce((sum, c) => sum + c.logicErrors, 0);

    return {
      totalChapters,
      solidChapters,
      issueChapters,
      brokenConnections,
      totalLogicErrors,
      completionPercent: Math.round((solidChapters / totalChapters) * 100),
    };
  }, [graphData]);

  if (isLoading) {
    return (
      <div className="h-[600px] glass-panel rounded-2xl flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
          <p className="text-[#8A8F98]">Loading thesis graph...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Stats */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Link2 className="w-5 h-5 text-purple-400" />
            Living Thesis Graph
          </h2>
          <p className="text-sm text-[#8A8F98] mt-1">
            {graphData?.lastAnalyzed
              ? `Last analyzed: ${new Date(graphData.lastAnalyzed).toLocaleString()}`
              : 'Real-time argument flow visualization'}
          </p>
        </div>

        <button
          onClick={fetchGraphData}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-sm text-white"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-5 gap-4">
          <div className="glass-panel rounded-xl p-4">
            <p className="text-xs text-[#8A8F98] uppercase tracking-wider">Chapters</p>
            <p className="text-2xl font-bold text-white mt-1">{stats.totalChapters}</p>
          </div>
          <div className="glass-panel rounded-xl p-4">
            <p className="text-xs text-[#8A8F98] uppercase tracking-wider">Solid</p>
            <p className="text-2xl font-bold text-green-400 mt-1">{stats.solidChapters}</p>
          </div>
          <div className="glass-panel rounded-xl p-4">
            <p className="text-xs text-[#8A8F98] uppercase tracking-wider">Issues</p>
            <p className="text-2xl font-bold text-red-400 mt-1">{stats.issueChapters}</p>
          </div>
          <div className="glass-panel rounded-xl p-4">
            <p className="text-xs text-[#8A8F98] uppercase tracking-wider">Logic Breaks</p>
            <p className="text-2xl font-bold text-orange-400 mt-1">{stats.brokenConnections}</p>
          </div>
          <div className="glass-panel rounded-xl p-4">
            <p className="text-xs text-[#8A8F98] uppercase tracking-wider">Progress</p>
            <p className="text-2xl font-bold text-purple-400 mt-1">{stats.completionPercent}%</p>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
          <AlertTriangle className="w-5 h-5 text-yellow-400" />
          <p className="text-sm text-yellow-200">
            {error} - Showing demo data
          </p>
        </div>
      )}

      {/* Graph Canvas */}
      <div className="h-[500px] glass-panel rounded-2xl overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.5}
          maxZoom={1.5}
          defaultEdgeOptions={{
            type: 'logic',
          }}
        >
          {/* SVG Filters */}
          <svg>
            <defs>
              <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
          </svg>

          <Background color="#1a1a1a" gap={20} size={1} />
          <Controls
            className="!bg-[#1a1a1a] !border-white/10 !rounded-lg"
            showInteractive={false}
          />
          <MiniMap
            className="!bg-[#1a1a1a] !border-white/10 !rounded-lg"
            nodeColor={(node) => {
              const status = (node.data as ChapterNodeData).status;
              return statusConfig[status].color;
            }}
            maskColor="rgba(0, 0, 0, 0.8)"
          />
        </ReactFlow>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-xs">
        {Object.entries(statusConfig).map(([key, config]) => (
          <div key={key} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: config.color }}
            />
            <span className="text-[#8A8F98]">{config.label}</span>
          </div>
        ))}
        <div className="w-px h-4 bg-white/10" />
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 bg-green-500" />
          <span className="text-[#8A8F98]">Solid Connection</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 bg-red-500 border-dashed" style={{ borderTop: '2px dashed #FF453A' }} />
          <span className="text-[#8A8F98]">Logic Break</span>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Demo Data (fallback when API unavailable)
// =============================================================================

function getDemoData(): ThesisGraphData {
  return {
    chapters: [
      {
        id: 'ch1',
        name: 'Chapter 1: Introduction',
        status: 'solid',
        lastSynced: new Date(Date.now() - 2 * 60000).toISOString(),
        logicErrors: 0,
        wordCount: 3500,
      },
      {
        id: 'ch2',
        name: 'Chapter 2: Literature Review',
        status: 'reviewing',
        lastSynced: new Date(Date.now() - 15 * 60000).toISOString(),
        logicErrors: 0,
        wordCount: 8200,
      },
      {
        id: 'ch3',
        name: 'Chapter 3: Methodology',
        status: 'solid',
        lastSynced: new Date(Date.now() - 60 * 60000).toISOString(),
        logicErrors: 0,
        wordCount: 5100,
      },
      {
        id: 'ch4',
        name: 'Chapter 4: Results',
        status: 'issues',
        lastSynced: new Date(Date.now() - 30 * 60000).toISOString(),
        logicErrors: 2,
        wordCount: 4800,
      },
      {
        id: 'ch5',
        name: 'Chapter 5: Discussion',
        status: 'draft',
        lastSynced: new Date(Date.now() - 120 * 60000).toISOString(),
        logicErrors: 0,
        wordCount: 2100,
      },
      {
        id: 'ch6',
        name: 'Chapter 6: Conclusion',
        status: 'issues',
        lastSynced: new Date(Date.now() - 180 * 60000).toISOString(),
        logicErrors: 3,
        wordCount: 1800,
      },
    ],
    connections: [
      { source: 'ch1', target: 'ch2', status: 'solid' },
      { source: 'ch2', target: 'ch3', status: 'solid' },
      { source: 'ch3', target: 'ch4', status: 'solid' },
      { source: 'ch4', target: 'ch5', status: 'broken', errorDescription: 'Results not adequately connected to discussion themes' },
      { source: 'ch5', target: 'ch6', status: 'broken', errorDescription: 'Missing link between discussion insights and conclusions' },
      { source: 'ch1', target: 'ch6', status: 'broken', errorDescription: 'Introduction claims not fully addressed in conclusion' },
    ],
    lastAnalyzed: new Date().toISOString(),
    overallScore: 68,
  };
}

export default ThesisGraph;
