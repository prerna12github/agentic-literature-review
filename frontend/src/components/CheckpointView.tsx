import React, { useState, useEffect } from 'react';
import { 
  Check, 
  Trash2, 
  ExternalLink, 
  Sparkles, 
  Ban
} from 'lucide-react';
import type { PaperCandidate, DecisionPayload } from '../types';

interface CheckpointViewProps {
  papers: PaperCandidate[];
  prompt?: string;
  onSubmitDecision: (payload: DecisionPayload) => Promise<void>;
  isSubmitting: boolean;
}

export const CheckpointView: React.FC<CheckpointViewProps> = ({
  papers,
  prompt,
  onSubmitDecision,
  isSubmitting,
}) => {
  // All checked by default
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(
    new Set(papers.map((p) => p.index))
  );

  useEffect(() => {
    setSelectedIndices(new Set(papers.map((p) => p.index)));
  }, [papers]);

  const togglePaper = (idx: number) => {
    const next = new Set(selectedIndices);
    if (next.has(idx)) {
      next.delete(idx);
    } else {
      next.add(idx);
    }
    setSelectedIndices(next);
  };

  const selectAll = () => {
    setSelectedIndices(new Set(papers.map((p) => p.index)));
  };

  const deselectAll = () => {
    setSelectedIndices(new Set());
  };

  // Score badge color helper: 8–10 green, 5–7 amber, <5 gray
  const getScoreBadge = (score?: number | null) => {
    const val = score ?? 0;
    if (val >= 8) {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-300/60 dark:border-emerald-700/60">
          Score {val}/10
        </span>
      );
    }
    if (val >= 5) {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300 border border-amber-300/60 dark:border-amber-700/60">
          Score {val}/10
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
        Score {val}/10
      </span>
    );
  };

  // PDF status chip: "PDF ✓" green / "abstract only" gray
  const getPdfChip = (status: string) => {
    if (status === 'downloaded') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60">
          <span>PDF ✓</span>
        </span>
      );
    }
    if (status === 'abstract_only') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
          <span>Abstract Only</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
        <span>Not Downloaded</span>
      </span>
    );
  };

  const handleApproveAll = async () => {
    await onSubmitDecision({ action: 'approve_all' });
  };

  const handleRemoveSelected = async () => {
    // Candidates whose boxes are UNCHECKED will be removed
    const allIndices = papers.map((p) => p.index);
    const removeList = allIndices.filter((idx) => !selectedIndices.has(idx));
    
    if (removeList.length === 0) {
      // Nothing removed -> approve all
      await onSubmitDecision({ action: 'approve_all' });
    } else {
      await onSubmitDecision({ action: 'remove', remove: removeList });
    }
  };

  const handleAbort = async () => {
    if (window.confirm('Are you sure you want to abort this review pipeline?')) {
      await onSubmitDecision({ action: 'abort' });
    }
  };

  // Button disabled if no checkboxes are unchecked
  const uncheckedCount = papers.length - selectedIndices.size;
  const isRemoveDisabled = uncheckedCount === 0 || isSubmitting;

  return (
    <div className="w-full space-y-6 pb-28">
      {/* Top Banner */}
      <div className="p-5 sm:p-6 rounded-2xl bg-amber-50/80 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/60 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-amber-500 text-white shrink-0 shadow-sm shadow-amber-500/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Human Checkpoint Gate
                </h3>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-200 font-semibold border border-amber-300 dark:border-amber-700">
                  Action Required
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 max-w-2xl leading-relaxed">
                {prompt || 'Review and curate the candidate papers ranked by the Filter Agent. Uncheck any irrelevant papers you wish to discard before the Reader Agent parses full text.'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto">
            <button
              onClick={handleAbort}
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50 border border-rose-200 dark:border-rose-900 transition cursor-pointer"
            >
              <Ban className="w-3.5 h-3.5" />
              <span>Abort</span>
            </button>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-amber-200/60 dark:border-amber-800/40 text-xs">
          <div className="flex items-center gap-3 text-slate-600 dark:text-slate-400">
            <span>
              <strong className="text-slate-900 dark:text-white">{selectedIndices.size}</strong> of {papers.length} approved
            </span>
            <span>•</span>
            <button
              onClick={selectAll}
              className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium cursor-pointer"
            >
              Select All
            </button>
            <button
              onClick={deselectAll}
              className="text-slate-500 hover:underline cursor-pointer"
            >
              Deselect All
            </button>
          </div>

          <span className="text-slate-500 text-[11px] hidden sm:inline">
            Ranked by Filter Agent (Gemini)
          </span>
        </div>
      </div>

      {/* Cards List */}
      <div className="space-y-3">
        {papers.map((paper) => {
          const isChecked = selectedIndices.has(paper.index);
          const scholarUrl = `https://scholar.google.com/scholar?q=${encodeURIComponent(paper.title)}`;

          return (
            <div
              key={paper.index}
              onClick={() => togglePaper(paper.index)}
              className={`p-4 sm:p-5 rounded-2xl border transition-all cursor-pointer ${
                isChecked
                  ? 'bg-white dark:bg-slate-900 border-slate-200/90 dark:border-slate-800 shadow-sm hover:border-indigo-400 dark:hover:border-indigo-500/60'
                  : 'bg-slate-50/70 dark:bg-slate-950/40 border-slate-200/60 dark:border-slate-800/40 opacity-60'
              }`}
            >
              <div className="flex items-start gap-4">
                {/* Pre-checked Checkbox */}
                <div className="pt-0.5">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => togglePaper(paper.index)}
                    onClick={(e) => e.stopPropagation()}
                    className="w-4 h-4 rounded border-slate-300 dark:border-slate-700 text-indigo-600 focus:ring-indigo-500 dark:bg-slate-800 cursor-pointer"
                  />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-baseline gap-2 mb-1">
                    <a
                      href={scholarUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-sm sm:text-base font-semibold text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 transition inline-flex items-center gap-1.5 group"
                    >
                      <span>{paper.title}</span>
                      <ExternalLink className="w-3.5 h-3.5 opacity-40 group-hover:opacity-100 shrink-0 text-indigo-500" />
                    </a>
                  </div>

                  {/* Metadata Chips */}
                  <div className="flex flex-wrap items-center gap-2 mt-2">
                    {paper.year && (
                      <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                        Year: {paper.year}
                      </span>
                    )}
                    {getPdfChip(paper.pdf_status)}
                  </div>

                  {/* One-line relevance reason */}
                  {paper.reason && (
                    <div className="mt-3 text-xs text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/60 p-2.5 rounded-xl border border-slate-200/70 dark:border-slate-700/60 leading-relaxed font-sans">
                      <span className="font-semibold text-slate-900 dark:text-slate-200">Relevance reason: </span>
                      {paper.reason}
                    </div>
                  )}
                </div>

                {/* Big Relevance Score Badge */}
                <div className="shrink-0 flex flex-col items-end">
                  {getScoreBadge(paper.score)}
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 mt-1 font-mono">
                    #{paper.index + 1}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Sticky Bottom Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-white/90 dark:bg-slate-900/90 border-t border-slate-200 dark:border-slate-800 backdrop-blur-lg p-4 shadow-2xl">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-xs text-slate-600 dark:text-slate-400">
            <span>
              <strong className="text-slate-900 dark:text-white">{selectedIndices.size}</strong> papers selected for full-text reading.
            </span>
            {uncheckedCount > 0 && (
              <span className="ml-1 text-rose-600 dark:text-rose-400 font-medium">
                ({uncheckedCount} paper{uncheckedCount > 1 ? 's' : ''} will be removed)
              </span>
            )}
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {/* Remove selected button (disabled if no checkboxes are unchecked) */}
            <button
              onClick={handleRemoveSelected}
              disabled={isRemoveDisabled}
              className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900 hover:bg-rose-100 dark:hover:bg-rose-900/50 disabled:opacity-40 disabled:cursor-not-allowed transition cursor-pointer"
            >
              <Trash2 className="w-4 h-4" />
              <span>Remove unchecked ({uncheckedCount})</span>
            </button>

            {/* Approve all button */}
            <button
              onClick={handleApproveAll}
              disabled={isSubmitting}
              className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 shadow-md shadow-indigo-600/20 disabled:opacity-50 transition cursor-pointer"
            >
              <Check className="w-4 h-4" />
              <span>{isSubmitting ? 'Resuming...' : `Approve all (${papers.length})`}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
