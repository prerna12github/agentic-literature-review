import React from 'react';
import { 
  Search, 
  Scale, 
  Hand, 
  BookOpen, 
  Swords, 
  PenTool, 
  Check, 
  Loader2 
} from 'lucide-react';
import type { ReviewStatus } from '../types';

interface PipelineVisualizerProps {
  status: ReviewStatus;
  detail: string;
}

interface Step {
  id: string;
  name: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const STEPS: Step[] = [
  { id: 'search', name: 'Search', label: 'arXiv & Scholar', icon: Search, description: 'Retrieve candidates' },
  { id: 'filter', name: 'Filter', label: 'LLM Triage', icon: Scale, description: 'Score relevance 0-10' },
  { id: 'approval', name: 'Your Approval', label: 'Human Checkpoint', icon: Hand, description: 'Curate paper list' },
  { id: 'reader', name: 'Reader', label: 'PyMuPDF Parser', icon: BookOpen, description: 'Extract page claims' },
  { id: 'contradiction', name: 'Contradiction', label: 'Cross-Paper Check', icon: Swords, description: 'Detect discrepancies' },
  { id: 'writer', name: 'Writer', label: 'Evidence Synthesis', icon: PenTool, description: 'Cited literature review' },
];

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({ status, detail }) => {
  // Infer active step from status and detail text
  const getActiveStepIndex = (): number => {
    if (status === 'completed') return 6;
    if (status === 'awaiting_approval') return 2; // Hand / Approval
    if (status === 'failed' || status === 'aborted') {
      const lower = detail.toLowerCase();
      if (lower.includes('write') || lower.includes('synthesis')) return 5;
      if (lower.includes('contradiction') || lower.includes('conflict')) return 4;
      if (lower.includes('read') || lower.includes('claim')) return 3;
      if (lower.includes('filter') || lower.includes('score')) return 1;
      return 0;
    }

    // running or starting
    const lower = detail.toLowerCase();
    if (lower.includes('writing') || lower.includes('synthesis') || lower.includes('final')) return 5;
    if (lower.includes('contradiction') || lower.includes('conflict')) return 4;
    if (lower.includes('reading') || lower.includes('claim') || lower.includes('chunk') || lower.includes('extract')) return 3;
    if (lower.includes('checkpoint') || lower.includes('resumed') || lower.includes('approval')) return 2;
    if (lower.includes('filter') || lower.includes('scoring') || lower.includes('rank')) return 1;
    if (lower.includes('search') || lower.includes('arxiv') || lower.includes('scholar') || lower.includes('retriev')) return 0;

    return 0;
  };

  const activeIndex = getActiveStepIndex();

  return (
    <div className="w-full bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-5 border-b border-slate-100 dark:border-slate-800/80">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Autonomous Multi-Agent Pipeline
          </h2>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            5 specialized agents coordinated via LangGraph with an explicit Human Checkpoint
          </p>
        </div>

        {/* Live Activity Line */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 max-w-md">
          {status === 'running' || status === 'starting' ? (
            <Loader2 className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400 animate-spin shrink-0" />
          ) : (
            <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
          )}
          <span className="text-xs text-slate-700 dark:text-slate-300 truncate font-mono">
            {detail || 'Pipeline initialized...'}
          </span>
        </div>
      </div>

      {/* Pipeline Node Graph */}
      <div className="pt-6 pb-2 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[680px] px-2">
          {STEPS.map((step, idx) => {
            const Icon = step.icon;
            const isCompleted = activeIndex > idx;
            const isCurrent = activeIndex === idx && status !== 'completed';
            const isCheckpoint = step.id === 'approval';

            return (
              <React.Fragment key={step.id}>
                {/* Node */}
                <div className="flex flex-col items-center text-center relative group min-w-[90px]">
                  
                  {/* Step Bubble */}
                  <div
                    className={`relative w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 ${
                      isCompleted
                        ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/20'
                        : isCurrent
                        ? isCheckpoint
                          ? 'bg-amber-500 text-white ring-4 ring-amber-500/25 shadow-lg shadow-amber-500/30 animate-pulse'
                          : 'bg-indigo-600 text-white ring-4 ring-indigo-500/25 shadow-lg shadow-indigo-600/30'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 border border-slate-200 dark:border-slate-700/60'
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="w-5 h-5 stroke-[2.5]" />
                    ) : (
                      <Icon className="w-5 h-5" />
                    )}

                    {/* Step number badge */}
                    <span className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-[9px] font-mono font-bold flex items-center justify-center text-slate-600 dark:text-slate-300">
                      {idx + 1}
                    </span>
                  </div>

                  {/* Node Labels */}
                  <div className="mt-3">
                    <p
                      className={`text-xs font-semibold leading-tight ${
                        isCurrent
                          ? isCheckpoint
                            ? 'text-amber-600 dark:text-amber-400'
                            : 'text-indigo-600 dark:text-indigo-400'
                          : isCompleted
                          ? 'text-slate-900 dark:text-white font-medium'
                          : 'text-slate-400 dark:text-slate-500'
                      }`}
                    >
                      {step.name}
                    </p>
                    <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 whitespace-nowrap">
                      {step.label}
                    </p>
                  </div>
                </div>

                {/* Connecting arrow / line between nodes */}
                {idx < STEPS.length - 1 && (
                  <div className="flex-1 mx-2 flex items-center justify-center relative">
                    <div
                      className={`h-0.5 w-full transition-all duration-500 ${
                        activeIndex > idx
                          ? 'bg-emerald-500'
                          : activeIndex === idx
                          ? 'bg-gradient-to-r from-indigo-500 to-slate-200 dark:to-slate-700'
                          : 'bg-slate-200 dark:bg-slate-800'
                      }`}
                    />
                    <div
                      className={`w-1.5 h-1.5 rounded-full absolute right-0 -translate-y-[0.5px] ${
                        activeIndex > idx ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-700'
                      }`}
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};
