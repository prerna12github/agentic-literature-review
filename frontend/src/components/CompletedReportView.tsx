import React, { useMemo, useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Download,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Quote,
  ChevronDown,
  Printer,
  FileCode,
  Globe,
  AlignLeft,
  Loader2,
  Check,
} from 'lucide-react';
import {
  exportToMarkdown,
  exportToDocx,
  exportToPdf,
  exportToHtml,
  exportToPlainText,
  printReport,
  type ExportFormat,
} from '../utils/exportReport';

interface CompletedReportViewProps {
  reportMarkdown: string;
  query: string;
  reviewId: string;
}

interface FormatOption {
  id: ExportFormat;
  label: string;
  extension: string;
  badgeBg: string;
  badgeText: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const FORMAT_OPTIONS: FormatOption[] = [
  {
    id: 'pdf',
    label: 'PDF Document',
    extension: '.pdf',
    badgeBg: 'bg-rose-100 dark:bg-rose-950/80',
    badgeText: 'text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/60',
    description: 'Academic formatted document with margins & citations',
    icon: FileText,
  },
  {
    id: 'docx',
    label: 'Word Document',
    extension: '.docx',
    badgeBg: 'bg-blue-100 dark:bg-blue-950/80',
    badgeText: 'text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800/60',
    description: 'Editable Microsoft Word document with headings & lists',
    icon: FileText,
  },
  {
    id: 'md',
    label: 'Markdown Source',
    extension: '.md',
    badgeBg: 'bg-indigo-100 dark:bg-indigo-950/80',
    badgeText: 'text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800/60',
    description: 'Raw markdown with inline scholarly citations',
    icon: FileCode,
  },
  {
    id: 'html',
    label: 'HTML Webpage',
    extension: '.html',
    badgeBg: 'bg-amber-100 dark:bg-amber-950/80',
    badgeText: 'text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/60',
    description: 'Standalone styled HTML file readable in any browser',
    icon: Globe,
  },
  {
    id: 'txt',
    label: 'Plain Text',
    extension: '.txt',
    badgeBg: 'bg-slate-100 dark:bg-slate-800',
    badgeText: 'text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700',
    description: 'Clean text stripped of markdown syntax',
    icon: AlignLeft,
  },
];

export const CompletedReportView: React.FC<CompletedReportViewProps> = ({
  reportMarkdown,
  query,
  reviewId,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<ExportFormat | null>(null);
  const [lastDownloaded, setLastDownloaded] = useState<ExportFormat | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside or escape key
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setDropdownOpen(false);
      }
    }

    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [dropdownOpen]);

  // Derive stats from markdown
  const stats = useMemo(() => {
    const conflictMatches = reportMarkdown.match(/\b(conflict|contradiction)s?\b/gi);
    const conflictsCount = conflictMatches ? conflictMatches.length : 0;

    const citationMatches = reportMarkdown.match(
      /\([A-Z][a-zA-Z\s]+(?:et\sal\.)?,?\s\d{4}(?:,\sp\.\s\d+)?\)/g
    );
    const citationsCount = citationMatches ? citationMatches.length : 0;

    const words = reportMarkdown.trim().split(/\s+/).length;

    return {
      conflictsCount,
      citationsCount,
      words,
    };
  }, [reportMarkdown]);

  // Handle export action
  const handleExport = async (format: ExportFormat) => {
    try {
      setExportingFormat(format);
      const opts = { markdown: reportMarkdown, query, reviewId };

      if (format === 'pdf') {
        exportToPdf(opts);
      } else if (format === 'docx') {
        await exportToDocx(opts);
      } else if (format === 'md') {
        exportToMarkdown(opts);
      } else if (format === 'html') {
        exportToHtml(opts);
      } else if (format === 'txt') {
        exportToPlainText(opts);
      } else if (format === 'print') {
        printReport();
      }

      setLastDownloaded(format);
      setTimeout(() => setLastDownloaded(null), 3000);
    } catch (err) {
      console.error(`Export failed for format ${format}:`, err);
    } finally {
      setTimeout(() => {
        setExportingFormat(null);
        setDropdownOpen(false);
      }, 350);
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Top Banner with Stats & Multi-Format Download */}
      <div className="no-print bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-100 dark:border-slate-800/80">
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

          {/* Download Action Dropdown Button */}
          <div className="relative" ref={dropdownRef}>
            <button
              type="button"
              onClick={() => setDropdownOpen((prev) => !prev)}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 shadow-sm shadow-indigo-600/20 transition cursor-pointer"
            >
              {exportingFormat ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
              <span>Download Report</span>
              <ChevronDown
                className={`w-3.5 h-3.5 transition-transform duration-200 ${
                  dropdownOpen ? 'rotate-180' : ''
                }`}
              />
            </button>

            {/* Format Selection Dropdown Popover */}
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-76 sm:w-84 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl p-2 z-50 animate-in fade-in zoom-in-95 duration-150">
                <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800/80 mb-1">
                  <p className="text-xs font-bold text-slate-900 dark:text-white">
                    Export Report
                  </p>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Select document format to download
                  </p>
                </div>

                <div className="space-y-0.5">
                  {FORMAT_OPTIONS.map((fmt) => {
                    const Icon = fmt.icon;
                    const isBusy = exportingFormat === fmt.id;
                    const isDone = lastDownloaded === fmt.id;

                    return (
                      <button
                        key={fmt.id}
                        type="button"
                        onClick={() => handleExport(fmt.id)}
                        disabled={exportingFormat !== null}
                        className="w-full flex items-start gap-3 p-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/70 text-left transition group cursor-pointer disabled:opacity-50"
                      >
                        <div className="mt-0.5 p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 shrink-0">
                          {isBusy ? (
                            <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
                          ) : isDone ? (
                            <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                          ) : (
                            <Icon className="w-4 h-4" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-1">
                            <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                              {fmt.label}
                            </span>
                            <span
                              className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-md ${fmt.badgeBg} ${fmt.badgeText}`}
                            >
                              {fmt.extension}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-tight">
                            {fmt.description}
                          </p>
                        </div>
                      </button>
                    );
                  })}

                  {/* Native Print Option */}
                  <div className="pt-1.5 border-t border-slate-100 dark:border-slate-800/80 mt-1">
                    <button
                      type="button"
                      onClick={() => handleExport('print')}
                      disabled={exportingFormat !== null}
                      className="w-full flex items-start gap-3 p-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/70 text-left transition group cursor-pointer disabled:opacity-50"
                    >
                      <div className="mt-0.5 p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 shrink-0">
                        <Printer className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                          Print / Browser PDF
                        </span>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-tight">
                          Open native system print dialog
                        </p>
                      </div>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
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
                    const parts = child.split(
                      /(\b(?:conflict|contradiction)s?\b|\([A-Za-z\s]+et\sal\.,?\s\d{4}(?:,\sp\.\s\d+)?\))/gi
                    );
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
            {reportMarkdown}
          </ReactMarkdown>
        </article>
      </div>
    </div>
  );
};
