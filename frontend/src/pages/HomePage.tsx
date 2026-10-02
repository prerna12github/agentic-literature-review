import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowRight, 
  Loader2, 
  HelpCircle,
  Sparkles,
  Bot,
  Scale,
  Hand,
  BookOpen,
  Swords,
  PenTool
} from 'lucide-react';
import { createReview } from '../api';
import { useToast } from '../context/ToastContext';
import { useReviews } from '../context/ReviewsContext';

const EXAMPLE_QUERIES = [
  'What are the state-of-the-art approaches to long-context window scaling in Transformers?',
  'How do quantum error mitigation strategies compare for near-term NISQ devices?',
  'What are the most effective techniques for reducing hallucinations in retrieval-augmented generation?',
  'A comparative analysis of deep learning architectures for network intrusion detection systems',
];

const AGENT_PIPELINE = [
  { name: 'Search', icon: Bot, desc: 'Scours arXiv & Semantic Scholar' },
  { name: 'Filter', icon: Scale, desc: 'LLM relevance ranking' },
  { name: 'Checkpoint', icon: Hand, desc: 'Human approval gate' },
  { name: 'Reader', icon: BookOpen, desc: 'Full-text PDF claim extraction' },
  { name: 'Contradiction', icon: Swords, desc: 'Cross-paper consensus & conflict' },
  { name: 'Writer', icon: PenTool, desc: 'Synthesized cited report' },
];

export const HomePage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { showToast } = useToast();
  const { refreshReviews } = useReviews();
  const navigate = useNavigate();

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
      // Refresh sidebar list
      refreshReviews();
      navigate(`/review/${encodeURIComponent(res.review_id)}`);
    } catch (err: any) {
      showToast(err.message || 'Failed to start review', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-16 space-y-12">
      
      {/* 1. Centered Hero Section */}
      <section className="text-center space-y-6 max-w-2xl mx-auto">
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-tight">
          Five AI agents. One human checkpoint.{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-teal-500">
            Every claim cited.
          </span>
        </h1>

        <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400 leading-relaxed max-w-xl mx-auto">
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
                Past reviews are accessible anytime in the left sidebar
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

      {/* 2. Pipeline Features Card */}
      <section className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xs">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white uppercase tracking-wider">
            Agentic Literature Review Pipeline
          </h2>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2">
          {AGENT_PIPELINE.map((agent, i) => {
            const Icon = agent.icon;
            return (
              <div
                key={i}
                className="p-3.5 rounded-xl bg-slate-50/70 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 space-y-1.5"
              >
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-xs font-bold text-slate-900 dark:text-white">
                    {agent.name}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
                  {agent.desc}
                </p>
              </div>
            );
          })}
        </div>
      </section>

    </div>
  );
};
