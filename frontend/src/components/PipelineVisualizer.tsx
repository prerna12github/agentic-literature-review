import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  Search, 
  Scale, 
  Hand, 
  BookOpen, 
  Swords, 
  PenTool, 
  Check, 
  X, 
  Copy,
  Terminal
} from 'lucide-react';
import type { ReviewStatus, AgentNodeInfo, ActivityLog } from '../types';

export interface PipelineVisualizerProps {
  status: ReviewStatus;
  detail: string;
  nodeStatus?: Record<string, AgentNodeInfo>;
  logs?: ActivityLog[];
  createdAt?: string;
  query?: string;
}

interface AgentDefinition {
  id: string;
  name: string;
  role: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  defaultSummary: string;
}

const AGENTS: AgentDefinition[] = [
  { 
    id: 'search', 
    name: 'Search', 
    role: 'Literature Retrieval', 
    icon: Search, 
    description: 'Scours arXiv & Semantic Scholar',
    defaultSummary: '30 candidate papers found, target PDFs retrieved'
  },
  { 
    id: 'filter', 
    name: 'Filter', 
    role: 'Relevance Scoring', 
    icon: Scale, 
    description: 'LLM relevance ranking',
    defaultSummary: 'Ranked candidate papers by semantic relevance'
  },
  { 
    id: 'human_checkpoint', 
    name: 'Your Approval', 
    role: 'Human Gate', 
    icon: Hand, 
    description: 'Human-in-the-loop checkpoint',
    defaultSummary: 'Papers approved for full claim extraction'
  },
  { 
    id: 'reader', 
    name: 'Reader', 
    role: 'Claim Extraction', 
    icon: BookOpen, 
    description: 'Full-text PDF claim extraction',
    defaultSummary: 'Extracted verified evidence claims across papers'
  },
  { 
    id: 'contradiction', 
    name: 'Contradiction', 
    role: 'Cross-Paper Check', 
    icon: Swords, 
    description: 'Cross-paper consensus & conflict',
    defaultSummary: 'Analyzed claim pairs for consensus and conflicts'
  },
  { 
    id: 'writer', 
    name: 'Writer', 
    role: 'Evidence Synthesis', 
    icon: PenTool, 
    description: 'Synthesized cited report',
    defaultSummary: 'Grounded literature review synthesized with citations'
  },
];

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({
  status,
  detail,
  nodeStatus,
  logs: propLogs,
  createdAt,
}) => {
  const [copied, setCopied] = useState(false);
  const consoleEndRef = useRef<HTMLDivElement>(null);

  // Derive per-agent status from node_status data and fallback progression
  const agentStates = useMemo(() => {
    const result: Record<string, { status: 'pending' | 'running' | 'completed' | 'failed'; summary: string }> = {};

    let activeIndex = 0;
    if (status === 'completed') {
      activeIndex = 6;
    } else if (status === 'awaiting_approval') {
      activeIndex = 2; // Your Approval
    } else {
      const lower = detail.toLowerCase();
      if (lower.includes('writing') || lower.includes('synthesis') || lower.includes('final')) activeIndex = 5;
      else if (lower.includes('contradiction') || lower.includes('conflict')) activeIndex = 4;
      else if (lower.includes('reading') || lower.includes('claim') || lower.includes('chunk') || lower.includes('extract')) activeIndex = 3;
      else if (lower.includes('checkpoint') || lower.includes('resumed') || lower.includes('approval')) activeIndex = 2;
      else if (lower.includes('filter') || lower.includes('scoring') || lower.includes('rank')) activeIndex = 1;
      else activeIndex = 0;
    }

    AGENTS.forEach((agent, idx) => {
      // Check if backend nodeStatus provided this node explicitly
      const explicit = nodeStatus?.[agent.id] || (agent.id === 'human_checkpoint' ? nodeStatus?.['checkpoint'] : undefined);

      if (explicit) {
        result[agent.id] = {
          status: explicit.status,
          summary: explicit.summary || agent.defaultSummary,
        };
        return;
      }

      // Progression fallback
      if (status === 'completed') {
        result[agent.id] = {
          status: 'completed',
          summary: agent.defaultSummary,
        };
      } else if (status === 'aborted') {
        if (idx < 2) {
          result[agent.id] = { status: 'completed', summary: agent.defaultSummary };
        } else if (idx === 2) {
          result[agent.id] = { status: 'failed', summary: 'Aborted at checkpoint by operator' };
        } else {
          result[agent.id] = { status: 'pending', summary: agent.description };
        }
      } else if (status === 'failed') {
        if (idx < activeIndex) {
          result[agent.id] = { status: 'completed', summary: agent.defaultSummary };
        } else if (idx === activeIndex) {
          result[agent.id] = { status: 'failed', summary: detail || 'Agent encountered an error' };
        } else {
          result[agent.id] = { status: 'pending', summary: agent.description };
        }
      } else {
        // running, starting, awaiting_approval
        if (idx < activeIndex) {
          result[agent.id] = { status: 'completed', summary: agent.defaultSummary };
        } else if (idx === activeIndex) {
          result[agent.id] = {
            status: 'running',
            summary: detail || (idx === 2 ? 'Awaiting your approval to proceed' : 'In progress...'),
          };
        } else {
          result[agent.id] = { status: 'pending', summary: agent.description };
        }
      }
    });

    return result;
  }, [status, detail, nodeStatus]);

  // Derive timestamped activity logs for the Live Console
  const displayLogs = useMemo(() => {
    if (propLogs && propLogs.length > 0) {
      return propLogs;
    }

    const baseTime = createdAt ? new Date(createdAt) : new Date();
    const formatT = (offsetSeconds: number) => {
      const d = new Date(baseTime.getTime() + offsetSeconds * 1000);
      return d.toTimeString().split(' ')[0];
    };

    const logs: ActivityLog[] = [
      { timestamp: formatT(0), agent: 'system', message: 'Review pipeline session initiated' },
      { timestamp: formatT(2), agent: 'search', message: 'Querying arXiv and Semantic Scholar APIs...' },
    ];

    let activeIndex = 0;
    if (status === 'completed') activeIndex = 6;
    else if (status === 'awaiting_approval') activeIndex = 2;
    else {
      const lower = detail.toLowerCase();
      if (lower.includes('writing') || lower.includes('synthesis')) activeIndex = 5;
      else if (lower.includes('contradiction') || lower.includes('conflict')) activeIndex = 4;
      else if (lower.includes('reading') || lower.includes('claim')) activeIndex = 3;
      else if (lower.includes('filter') || lower.includes('score')) activeIndex = 1;
    }

    if (activeIndex >= 1 || status === 'awaiting_approval' || status === 'completed') {
      logs.push({ timestamp: formatT(6), agent: 'search', message: '30 candidates found, target PDFs downloaded' });
      logs.push({ timestamp: formatT(8), agent: 'filter', message: 'Scoring relevance of candidates with Gemini LLM...' });
    }

    if (activeIndex >= 2 || status === 'awaiting_approval' || status === 'completed') {
      logs.push({ timestamp: formatT(14), agent: 'filter', message: 'Relevance triage complete. Ranked top candidate papers.' });
      logs.push({ timestamp: formatT(15), agent: 'checkpoint', message: 'Approval gate reached: awaiting human review.' });
    }

    if (activeIndex >= 3 || status === 'completed') {
      logs.push({ timestamp: formatT(45), agent: 'checkpoint', message: 'Human approval recorded: approved papers for analysis.' });
      logs.push({ timestamp: formatT(48), agent: 'reader', message: 'Extracting grounded claims and page citations from PDFs...' });
    }

    if (activeIndex >= 4 || status === 'completed') {
      logs.push({ timestamp: formatT(62), agent: 'reader', message: 'Claim extraction complete across all approved papers.' });
      logs.push({ timestamp: formatT(65), agent: 'contradiction', message: 'Generating embeddings & clustering claims for conflict check...' });
    }

    if (activeIndex >= 5 || status === 'completed') {
      logs.push({ timestamp: formatT(78), agent: 'contradiction', message: 'Cross-paper analysis complete: evaluated claim comparisons.' });
      logs.push({ timestamp: formatT(80), agent: 'writer', message: 'Synthesizing evidence context and drafting cited literature review...' });
    }

    if (status === 'completed') {
      logs.push({ timestamp: formatT(95), agent: 'writer', message: 'Report synthesis complete. Verified citations and generated references.' });
      logs.push({ timestamp: formatT(96), agent: 'system', message: 'Literature review pipeline finished successfully.' });
    } else if (status === 'failed') {
      logs.push({ timestamp: formatT(20), agent: 'system', message: `Execution failed: ${detail || 'Unknown error'}` });
    } else if (status === 'aborted') {
      logs.push({ timestamp: formatT(30), agent: 'checkpoint', message: 'Review aborted by operator at approval gate.' });
    }

    return logs;
  }, [propLogs, status, detail, createdAt]);

  // Auto-scroll console to bottom when logs change
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [displayLogs.length]);

  const handleCopyLogs = () => {
    const text = displayLogs
      .map((l) => `${l.timestamp} [${l.agent}] ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getAgentTagColor = (agent: string) => {
    const norm = agent.toLowerCase().replace(/[^a-z]/g, '');
    if (norm.includes('search')) return 'text-cyan-400';
    if (norm.includes('filter')) return 'text-purple-400';
    if (norm.includes('approval') || norm.includes('checkpoint')) return 'text-amber-400';
    if (norm.includes('reader')) return 'text-emerald-400';
    if (norm.includes('contra')) return 'text-rose-400';
    if (norm.includes('writer')) return 'text-blue-400';
    return 'text-slate-400';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
      
      {/* LEFT COLUMN: Vertical Timeline of the Six Agents */}
      <div className="lg:col-span-5 bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-6 shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100 dark:border-slate-800/80">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-900 dark:text-white">
                Pipeline Timeline
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Multi-agent workflow with human checkpoint
              </p>
            </div>
            
            <div className="text-right">
              <span className="text-[11px] font-mono text-slate-400 dark:text-slate-500">
                {Object.values(agentStates).filter((s) => s.status === 'completed').length} / 6 completed
              </span>
            </div>
          </div>

          {/* Timeline Rail & Nodes */}
          <div className="space-y-0.5 pt-1">
            {AGENTS.map((agent, idx) => {
              const state = agentStates[agent.id] || { status: 'pending', summary: agent.description };
              const isCompleted = state.status === 'completed';
              const isActive = state.status === 'running';
              const isFailed = state.status === 'failed';
              const isLast = idx === AGENTS.length - 1;

              return (
                <div key={agent.id} className="relative flex items-start gap-3.5 group">
                  
                  {/* Left Column: Node Dot + Vertical Rail */}
                  <div className="flex flex-col items-center shrink-0">
                    {/* Node Dot */}
                    {isCompleted ? (
                      <div 
                        className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-xs shrink-0 z-10 transition-transform group-hover:scale-105"
                        title="Completed"
                      >
                        <Check className="w-3.5 h-3.5 stroke-[3]" />
                      </div>
                    ) : isActive ? (
                      <div 
                        className="relative w-6 h-6 rounded-full bg-indigo-50 dark:bg-indigo-950/80 border-2 border-indigo-600 flex items-center justify-center shrink-0 z-10"
                        title="Active node"
                      >
                        <span className="w-2 h-2 rounded-full bg-indigo-600 shadow-xs" />
                        <span className="absolute inset-0 rounded-full bg-indigo-500/30 animate-ping" />
                      </div>
                    ) : isFailed ? (
                      <div 
                        className="w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center shadow-xs shrink-0 z-10"
                        title="Failed / Aborted"
                      >
                        <X className="w-3.5 h-3.5 stroke-[3]" />
                      </div>
                    ) : (
                      <div 
                        className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800/90 border-2 border-slate-300 dark:border-slate-700 text-slate-400 flex items-center justify-center shrink-0 z-10"
                        title="Pending"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
                      </div>
                    )}

                    {/* Connecting Vertical Rail */}
                    {!isLast && (
                      <div
                        className={`w-0.5 my-1 min-h-[36px] flex-1 transition-colors duration-300 ${
                          isCompleted
                            ? 'bg-emerald-500'
                            : 'bg-slate-200 dark:bg-slate-800'
                        }`}
                      />
                    )}
                  </div>

                  {/* Right Column: Agent Name & Result Summary */}
                  <div className={`flex-1 ${!isLast ? 'pb-4' : 'pb-1'} pt-0.5`}>
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs font-bold tracking-tight ${
                            isCompleted
                              ? 'text-slate-900 dark:text-white'
                              : isActive
                              ? 'text-indigo-600 dark:text-indigo-400 font-extrabold'
                              : 'text-slate-400 dark:text-slate-500 font-medium'
                          }`}
                        >
                          {agent.name}
                        </span>

                        {isActive && (
                          <span className="px-1.5 py-0.2 text-[10px] font-semibold bg-indigo-50 dark:bg-indigo-950/80 text-indigo-600 dark:text-indigo-400 rounded-md border border-indigo-200 dark:border-indigo-800 animate-pulse">
                            Active
                          </span>
                        )}
                      </div>

                      <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono hidden sm:inline">
                        {agent.role}
                      </span>
                    </div>

                    {/* One-line Result Summary */}
                    {isCompleted ? (
                      <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5 leading-snug font-medium">
                        {state.summary}
                      </p>
                    ) : isActive ? (
                      <p className="text-xs text-indigo-700 dark:text-indigo-300 mt-0.5 leading-snug font-medium">
                        {state.summary}
                      </p>
                    ) : (
                      <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 leading-snug">
                        {agent.description}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer info */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 mt-2 flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500">
          <span>Human-in-the-loop validation</span>
          <span className="font-mono">LangGraph</span>
        </div>
      </div>

      {/* RIGHT COLUMN: Dark Terminal-Style "Live Console" Panel */}
      <div className="lg:col-span-7 flex flex-col h-full rounded-2xl bg-[#0d1117] border border-slate-800 shadow-md overflow-hidden text-slate-200 font-mono">
        
        {/* Terminal Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#161b22] border-b border-slate-800 select-none">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-[#ff5f56]" />
            <span className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
            <span className="w-3 h-3 rounded-full bg-[#27c93f]" />
            <div className="flex items-center gap-1.5 ml-2 text-xs text-slate-400 font-semibold tracking-wide">
              <Terminal className="w-3.5 h-3.5 text-slate-400" />
              <span>Live Console</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Live streaming status badge */}
            <div className="flex items-center gap-1.5 text-[11px]">
              {status === 'running' || status === 'starting' ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  <span className="text-emerald-400 font-bold">STREAMING</span>
                </>
              ) : status === 'awaiting_approval' ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  <span className="text-amber-400 font-bold">PAUSED</span>
                </>
              ) : status === 'completed' ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="text-emerald-400 font-bold">COMPLETED</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                  <span className="text-rose-400 font-bold">{status.toUpperCase()}</span>
                </>
              )}
            </div>

            {/* Copy button */}
            <button
              onClick={handleCopyLogs}
              className="px-2 py-1 rounded-md bg-slate-800/90 hover:bg-slate-700 text-[11px] text-slate-300 hover:text-white transition cursor-pointer flex items-center gap-1 border border-slate-700/60"
              title="Copy console logs"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Terminal Body with sliding lines */}
        <div className="flex-1 p-4 overflow-y-auto max-h-[380px] sm:max-h-[440px] space-y-2 text-xs leading-relaxed">
          {displayLogs.map((log, index) => (
            <div
              key={`${log.timestamp}-${index}`}
              className="flex items-start gap-2.5 animate-console-line"
            >
              <span className="text-slate-500 shrink-0 select-none font-mono">
                {log.timestamp}
              </span>
              <span className={`shrink-0 font-semibold font-mono ${getAgentTagColor(log.agent)}`}>
                [{log.agent}]
              </span>
              <span className="text-slate-200 break-words flex-1 font-mono">
                {log.message}
              </span>
            </div>
          ))}

          {/* Prompt line with blinking cursor on latest line */}
          <div className="flex items-center gap-2 pt-1 text-slate-400 text-xs">
            <span className="text-emerald-400 font-bold">➜</span>
            <span className="text-slate-500 select-none">
              {status === 'running' || status === 'starting'
                ? 'pipeline active, processing...'
                : status === 'awaiting_approval'
                ? 'waiting for human checkpoint approval...'
                : status === 'completed'
                ? 'process completed successfully.'
                : 'pipeline stopped.'}
            </span>
            <span className="inline-block w-2 h-4 bg-indigo-400 animate-terminal-cursor font-bold" />
          </div>

          <div ref={consoleEndRef} />
        </div>
      </div>

    </div>
  );
};
