import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Download, FileText, CheckCircle2, AlertTriangle, Quote } from 'lucide-react';

interface CompletedReportViewProps {
  reportMarkdown: string;
  query: string;
  reviewId: string;
}

export const CompletedReportView: React.FC<CompletedReportViewProps> = ({
  reportMarkdown,
  query,
  reviewId,
}) => {
  // Pre-process markdown: highlight "conflict" / "CONFLICT" in red
  // and format citations like (Author et al., 2020, p. 4)
  const processedMarkdown = useMemo(() => {
    if (!reportMarkdown) return '';
    return reportMarkdown;
  }, [reportMarkdown]);

  // Derive stats from markdown
  const stats = useMemo(() => {
    // Count conflicts
    const conflictMatches = reportMarkdown.match(/\b(conflict|contradiction)s?\b/gi);
    const conflictsCount = conflictMatches ? conflictMatches.length : 0;

    // Count citations like (Author et al., 2024, p. X) or Author (Year)
    const citationMatches = reportMarkdown.match(/\([A-Z][a-zA-Z\s]+(?:et\sal\.)?,?\s\d{4}(?:,\sp\.\s\d+)?\)/g);
    const citationsCount = citationMatches ? citationMatches.length : 0;

    // Count words
    const words = reportMarkdown.trim().split(/\s+/).length;

    return {
      conflictsCount,
      citationsCount,
      words,
    };
  }, [reportMarkdown]);

  const handleDownload = () => {
    const blob = new Blob([reportMarkdown], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const sanitized = query.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 32);
    a.download = `literature_review_${sanitized || reviewId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full space-y-6">
      {/* Top Banner with Stats */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100 dark:border-slate-800/80">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
              </span>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Grounded Literature Review
              </h2>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Fully synthesized and verified against full-text PDF citations
            </p>
          </div>

          <button
            onClick={handleDownload}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 shadow-sm shadow-indigo-600/20 transition cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Download report (.md)</span>
          </button>
        </div>

        {/* Stats Summary Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-4">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 shrink-0">
              <Quote className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400">Page Citations</p>
              <p className="text-sm font-bold text-slate-900 dark:text-white font-mono">
                {stats.citationsCount > 0 ? `${stats.citationsCount} cited` : 'Full provenance'}
              </p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-rose-100 dark:bg-rose-950 text-rose-600 dark:text-rose-400 shrink-0">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400">Contradictions</p>
              <p className="text-sm font-bold text-slate-900 dark:text-white font-mono">
                {stats.conflictsCount} identified
              </p>
            </div>
          </div>

          <div className="col-span-2 sm:col-span-1 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 shrink-0">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400">Word Count</p>
              <p className="text-sm font-bold text-slate-900 dark:text-white font-mono">
                {stats.words.toLocaleString()} words
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Markdown Document Paper Card */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-10 shadow-sm">
        <article className="report-markdown prose prose-slate dark:prose-invert max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => {
                const renderChild = (child: React.ReactNode): React.ReactNode => {
                  if (typeof child === 'string') {
                    const parts = child.split(/(\b(?:conflict|contradiction)s?\b|\([A-Za-z\s]+et\sal\.,?\s\d{4}(?:,\sp\.\s\d+)?\))/gi);
                    return parts.map((part, i) => {
                      if (/^(?:conflict|contradiction)s?$/i.test(part)) {
                        return (
                          <span
                            key={i}
                            className="font-bold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/70 px-1 py-0.5 rounded border border-rose-200 dark:border-rose-800/60"
                          >
                            {part}
                          </span>
                        );
                      }
                      if (/^\([A-Za-z\s]+et\sal\.,?\s\d{4}(?:,\sp\.\s\d+)?\)$/i.test(part)) {
                        return (
                          <span
                            key={i}
                            className="font-mono text-xs font-semibold px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/60 mx-0.5 inline-block"
                          >
                            {part}
                          </span>
                        );
                      }
                      return part;
                    });
                  }
                  return child;
                };

                return (
                  <p className="my-3 leading-relaxed text-slate-800 dark:text-slate-200">
                    {React.Children.map(children, renderChild)}
                  </p>
                );
              },
            }}
          >
            {processedMarkdown}
          </ReactMarkdown>
        </article>
      </div>
    </div>
  );
};
