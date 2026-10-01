import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowRight, 
  Loader2, 
  Clock, 
  HelpCircle,
  Search,
  BookOpen
} from 'lucide-react';
import { createReview, listReviews } from '../api';
import type { ReviewOut } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { useToast } from '../context/ToastContext';

const EXAMPLE_QUERIES = [
  'What are the state-of-the-art approaches to long-context window scaling in Transformers?',
  'How do quantum error mitigation strategies compare for near-term NISQ devices?',
  'What are the most effective techniques for reducing hallucinations in retrieval-augmented generation?',
  'A comparative analysis of deep learning architectures for network intrusion detection systems',
];

export const HomePage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [reviews, setReviews] = useState<ReviewOut[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [filterText, setFilterText] = useState('');
  
  const { showToast } = useToast();
  const navigate = useNavigate();

  const fetchHistory = async () => {
    try {
      const data = await listReviews();
      setReviews(data);
    } catch (err: any) {
      showToast(err.message || 'Failed to load past reviews', 'error');
    } finally {
      setIsLoadingList(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleStartReview = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) return;
    if (cleanQuery.length < 10) {
      showToast('Research question must be at least 10 characters long', 'info');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await createReview(cleanQuery);
      showToast('Literature review pipeline started!', 'success');
      navigate(`/review/${encodeURIComponent(res.review_id)}`);
    } catch (err: any) {
      showToast(err.message || 'Failed to start review', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredReviews = reviews.filter((r) =>
    r.query.toLowerCase().includes(filterText.toLowerCase()) ||
    r.review_id.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 space-y-16">
      
      {/* 1. Large Centered Hero */}
      <section className="text-center space-y-6 pt-4 sm:pt-8 max-w-3xl mx-auto">
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-tight">
          Five AI agents. One human checkpoint.{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-teal-500">
            Every claim cited.
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 leading-relaxed max-w-2xl mx-auto">
          From a research question to a rigorous literature review in minutes.
          Search papers on arXiv & Semantic Scholar, triage relevance, approve sources,
          extract grounded claims, detect conflicts, and generate a synthesized report.
        </p>

        {/* Input Textarea & Start Button */}
        <form onSubmit={handleStartReview} className="mt-8 text-left space-y-3">
          <div className="relative bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-700 p-2 sm:p-2.5 shadow-xl shadow-slate-200/50 dark:shadow-none focus-within:ring-2 focus-within:ring-indigo-500 focus-within:border-transparent transition">
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What research question do you want to explore? (e.g. Approaches to long-context scaling in transformer architectures)"
              className="w-full p-3 bg-transparent text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-sm sm:text-base resize-none focus:outline-none"
            />
            
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 pt-2 border-t border-slate-100 dark:border-slate-800/80">
              <span className="text-[11px] text-slate-400 dark:text-slate-500 pl-3 hidden sm:inline">
                Press button to launch background agent pipeline
              </span>

              <button
                type="submit"
                disabled={isSubmitting || query.trim().length < 5}
                className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-sm text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 shadow-md shadow-indigo-600/20 disabled:opacity-50 disabled:cursor-not-allowed transition cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Launching Pipeline...</span>
                  </>
                ) : (
                  <>
                    <span>Start Review</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Example prompt chips */}
          <div className="pt-2">
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 flex items-center gap-1.5">
              <HelpCircle className="w-3.5 h-3.5 text-indigo-500" />
              <span>Or pick a prompt to test:</span>
            </p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_QUERIES.map((example, idx) => (
                <button
                  type="button"
                  key={idx}
                  onClick={() => setQuery(example)}
                  className="text-left text-xs px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/70 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 border border-slate-200 dark:border-slate-700/60 transition cursor-pointer"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </form>
      </section>

      {/* 2. Review History Section */}
      <section className="space-y-4 pt-4 border-t border-slate-200/80 dark:border-slate-800/80">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <span>Review History</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Select any past or running literature review to inspect agents and results
            </p>
          </div>

          {/* Filter search */}
          {reviews.length > 0 && (
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                placeholder="Filter reviews..."
                value={filterText}
                onChange={(e) => setFilterText(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          )}
        </div>

        {/* Reviews List / Table */}
        {isLoadingList ? (
          <div className="space-y-3">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 animate-pulse space-y-2.5"
              >
                <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/4"></div>
                <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        ) : reviews.length === 0 ? (
          <div className="text-center py-12 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 p-6 space-y-3">
            <BookOpen className="w-10 h-10 text-slate-400 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
              No literature reviews yet
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
              Ask your first research question above to initiate the 5-agent pipeline with human approval.
            </p>
          </div>
        ) : filteredReviews.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            No reviews matching "{filterText}"
          </div>
        ) : (
          <div className="space-y-3">
            {filteredReviews.map((r) => {
              const formattedDate = new Date(r.created_at).toLocaleString(undefined, {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              });

              return (
                <div
                  key={r.review_id}
                  onClick={() => navigate(`/review/${encodeURIComponent(r.review_id)}`)}
                  className="group p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-sm hover:border-indigo-400 dark:hover:border-indigo-500/70 hover:shadow-md transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={r.status} />
                      <span className="text-[11px] font-mono text-slate-400 dark:text-slate-500">
                        {r.review_id}
                      </span>
                      <span className="text-[11px] text-slate-400 dark:text-slate-500">
                        • {formattedDate}
                      </span>
                    </div>

                    <h3 className="text-sm sm:text-base font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition leading-snug">
                      {r.query}
                    </h3>

                    {r.detail && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                        {r.detail}
                      </p>
                    )}
                  </div>

                  <div className="shrink-0 flex items-center gap-2 text-xs font-medium text-indigo-600 dark:text-indigo-400 group-hover:translate-x-0.5 transition-transform">
                    <span>Inspect</span>
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

    </div>
  );
};
