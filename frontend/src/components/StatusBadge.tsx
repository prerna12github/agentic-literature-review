import React from 'react';
import type { ReviewStatus } from '../types';

interface StatusBadgeProps {
  status: ReviewStatus;
  showDot?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, showDot = true }) => {
  switch (status) {
    case 'starting':
    case 'running':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800/60">
          {showDot && (
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
          )}
          <span>{status === 'starting' ? 'Starting' : 'Running'}</span>
        </span>
      );

    case 'awaiting_approval':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60 animate-pulse">
          {showDot && (
            <span className="h-2 w-2 rounded-full bg-amber-500"></span>
          )}
          <span>Awaiting Approval</span>
        </span>
      );

    case 'completed':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60">
          {showDot && (
            <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
          )}
          <span>Completed</span>
        </span>
      );

    case 'failed':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60">
          {showDot && (
            <span className="h-2 w-2 rounded-full bg-rose-500"></span>
          )}
          <span>Failed</span>
        </span>
      );

    case 'aborted':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
          {showDot && (
            <span className="h-2 w-2 rounded-full bg-slate-400"></span>
          )}
          <span>Aborted</span>
        </span>
      );

    default:
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
          <span>{status}</span>
        </span>
      );
  }
};
