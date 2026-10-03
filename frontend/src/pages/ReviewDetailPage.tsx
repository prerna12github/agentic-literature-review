import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  RotateCw, 
  AlertOctagon, 
  Calendar, 
  ArrowLeft, 
  Loader2
} from 'lucide-react';
import { getReview, getPending, submitDecision, retryReview, getReport } from '../api';
import type { ReviewOut, PendingResponse, DecisionPayload } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { PipelineVisualizer } from '../components/PipelineVisualizer';
import { CheckpointView } from '../components/CheckpointView';
import { CompletedReportView } from '../components/CompletedReportView';
import { useToast } from '../context/ToastContext';
import confetti from 'canvas-confetti';

export const ReviewDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [review, setReview] = useState<ReviewOut | null>(null);
  const [pendingData, setPendingData] = useState<PendingResponse | null>(null);
  const [reportMarkdown, setReportMarkdown] = useState<string | null>(null);
  
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmittingDecision, setIsSubmittingDecision] = useState<boolean>(false);
  const [isRetrying, setIsRetrying] = useState<boolean>(false);

  const prevStatusRef = useRef<string | null>(null);
  const isFetchingPendingRef = useRef<boolean>(false);

  // Fetch pending checkpoint data
  const fetchPendingData = useCallback(async (reviewId: string) => {
    if (isFetchingPendingRef.current) return;
    isFetchingPendingRef.current = true;
    try {
      const data = await getPending(reviewId);
      setPendingData(data);
    } catch (err: any) {
      // 409 means status transitioned mid-poll
      if (err.status !== 409) {
        showToast(err.message || 'Failed to fetch candidate papers for checkpoint', 'error');
      }
    } finally {
      isFetchingPendingRef.current = false;
    }
  }, [showToast]);

  // Fetch final report
  const fetchReportData = useCallback(async (reviewId: string) => {
    try {
      const md = await getReport(reviewId);
      setReportMarkdown(md);
    } catch (err: any) {
      if (err.status !== 409) {
        showToast(err.message || 'Failed to fetch completed literature review report', 'error');
      }
    }
  }, [showToast]);

  // Fetch main review
  const fetchReview = useCallback(async (isInitial = false) => {
    if (!id) return;
    try {
      const data = await getReview(id);
      setReview(data);

      // Trigger confetti on transition to completed
      if (data.status === 'completed' && prevStatusRef.current && prevStatusRef.current !== 'completed') {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
        });
        showToast('Literature review synthesized successfully!', 'success');
      }
      prevStatusRef.current = data.status;

      // Handle specific states
      if (data.status === 'awaiting_approval') {
        await fetchPendingData(id);
      } else {
        setPendingData(null);
      }

      if (data.status === 'completed' && !reportMarkdown) {
        await fetchReportData(id);
      }
    } catch (err: any) {
      if (isInitial) {
        showToast(err.message || 'Failed to load review', 'error');
      }
    } finally {
      if (isInitial) setIsLoading(false);
    }
  }, [id, fetchPendingData, fetchReportData, reportMarkdown, showToast]);

  // Initial load
  useEffect(() => {
    fetchReview(true);
  }, [id]);

  // Polling every ~5 seconds while running or starting
  useEffect(() => {
    if (!review) return;
    const shouldPoll = review.status === 'starting' || review.status === 'running';
    if (!shouldPoll) return;

    const interval = setInterval(() => {
      fetchReview(false);
    }, 5000);

    return () => clearInterval(interval);
  }, [review?.status, fetchReview]);

  // Handle human decision
  const handleSubmitDecision = async (payload: DecisionPayload) => {
    if (!id) return;
    setIsSubmittingDecision(true);
    try {
      const updated = await submitDecision(id, payload);
      setReview(updated);
      setPendingData(null);
      showToast(
        payload.action === 'abort'
          ? 'Review pipeline aborted'
          : 'Decision recorded! Resuming pipeline at Reader agent...',
        payload.action === 'abort' ? 'info' : 'success'
      );
      // Immediately refresh review state
      await fetchReview(false);
    } catch (err: any) {
      showToast(err.message || 'Failed to submit decision', 'error');
    } finally {
      setIsSubmittingDecision(false);
    }
  };

  // Handle retry
  const handleRetry = async () => {
    if (!id) return;
    setIsRetrying(true);
    try {
      const updated = await retryReview(id);
      setReview(updated);
      showToast('Retrying review from checkpoint...', 'info');
      await fetchReview(false);
    } catch (err: any) {
      showToast(err.message || 'Failed to retry review', 'error');
    } finally {
      setIsRetrying(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-24 text-center space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600 dark:text-indigo-400 mx-auto" />
        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
          Loading review details...
        </p>
      </div>
    );
  }

  if (!review) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center space-y-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Review Not Found</h2>
        <p className="text-xs text-slate-500">
          The requested review ID does not exist in the database.
        </p>
        <button
          onClick={() => navigate('/')}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Reviews</span>
        </button>
      </div>
    );
  }

  const formattedDate = new Date(review.created_at).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      
      {/* Top Header Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={review.status} />
            <span className="text-xs font-mono text-slate-500 bg-slate-100 dark:bg-slate-800 px-2.5 py-0.5 rounded-md">
              {review.review_id}
            </span>
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              {formattedDate}
            </span>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              onClick={() => fetchReview(false)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition cursor-pointer"
              title="Refresh status"
            >
              <RotateCw className="w-3.5 h-3.5" />
              <span>Sync</span>
            </button>
          </div>
        </div>

        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white leading-tight">
            {review.query}
          </h1>
          {review.detail && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">
              Status log: {review.detail}
            </p>
          )}
        </div>
      </div>

      {/* Two-Column Progress Layout: Vertical Agent Timeline + Live Console */}
      <PipelineVisualizer
        status={review.status}
        detail={review.detail}
        nodeStatus={review.node_status}
        logs={review.logs}
        createdAt={review.created_at}
        query={review.query}
      />

      {/* STATE 1: FAILED STATE */}
      {review.status === 'failed' && (
        <div className="p-6 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-rose-600 text-white shrink-0">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-rose-900 dark:text-rose-200">
                Pipeline Failed
              </h3>
              <p className="text-xs text-rose-700 dark:text-rose-300 mt-1">
                {review.detail || 'An unexpected error occurred during execution.'}
              </p>
            </div>
          </div>

          <button
            onClick={handleRetry}
            disabled={isRetrying}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 shadow-md shadow-rose-600/20 disabled:opacity-50 transition cursor-pointer shrink-0"
          >
            <RotateCw className={`w-4 h-4 ${isRetrying ? 'animate-spin' : ''}`} />
            <span>{isRetrying ? 'Retrying...' : 'Retry Pipeline'}</span>
          </button>
        </div>
      )}

      {/* STATE 2: CHECKPOINT STATE (Awaiting Approval) */}
      {review.status === 'awaiting_approval' && pendingData && (
        <CheckpointView
          papers={pendingData.papers}
          prompt={pendingData.prompt}
          onSubmitDecision={handleSubmitDecision}
          isSubmitting={isSubmittingDecision}
        />
      )}

      {/* STATE 3: COMPLETED STATE (Stats Cards & Full Markdown Report) */}
      {review.status === 'completed' && reportMarkdown && (
        <CompletedReportView
          reportMarkdown={reportMarkdown}
          query={review.query}
          reviewId={review.review_id}
        />
      )}

      {/* STATE 4: RUNNING INFO */}
      {(review.status === 'starting' || review.status === 'running') && (
        <div className="p-8 text-center rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 space-y-3">
          <Loader2 className="w-7 h-7 animate-spin text-indigo-600 dark:text-indigo-400 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
            Agents Actively Working in Background
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
            This page polls every 5 seconds. When the pipeline pauses for your review, the Human Checkpoint approval station will appear automatically.
          </p>
        </div>
      )}

    </div>
  );
};
