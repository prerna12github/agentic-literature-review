import React from 'react';
import { BookOpen, Sun, Moon, ArrowLeft, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useReviews } from '../context/ReviewsContext';

export const Header: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { sidebarOpen, toggleSidebar } = useReviews();
  const location = useLocation();
  const isDetail = location.pathname.startsWith('/review/');

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200/80 dark:border-slate-800/80 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md transition-colors">
      <div className="w-full px-4 sm:px-6 h-16 flex items-center justify-between">
        
        {/* Left: Sidebar Toggle + Brand */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          <button
            onClick={toggleSidebar}
            className={`p-2 rounded-xl border transition-all cursor-pointer flex items-center justify-center ${
              !sidebarOpen
                ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white border-slate-300 dark:border-slate-700 shadow-xs'
                : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="w-4 h-4" />
            ) : (
              <PanelLeftOpen className="w-4 h-4" />
            )}
          </button>

          {isDetail && (
            <Link
              to="/"
              className="p-2 rounded-xl text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              title="Back to New Review"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
          )}

          <Link to="/" className="flex items-center space-x-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 flex items-center justify-center transition-colors">
              <BookOpen className="w-4 h-4" />
            </div>
            <div className="flex items-baseline space-x-1.5">
              <span className="font-semibold text-base tracking-tight text-slate-900 dark:text-white">
                LitReview
              </span>
            </div>
          </Link>
        </div>

        {/* Right: Light / Dark Toggle Switch */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center p-1 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700/80 text-xs">
            <button
              onClick={() => setTheme('light')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium transition cursor-pointer ${
                theme === 'light'
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
              }`}
              title="Switch to light theme"
              aria-label="Switch to light theme"
            >
              <Sun className={`w-3.5 h-3.5 ${theme === 'light' ? 'text-amber-500' : ''}`} />
              <span className="hidden sm:inline">Light</span>
            </button>

            <button
              onClick={() => setTheme('dark')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-medium transition cursor-pointer ${
                theme === 'dark'
                  ? 'bg-slate-900 text-white shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
              }`}
              title="Switch to dark theme"
              aria-label="Switch to dark theme"
            >
              <Moon className={`w-3.5 h-3.5 ${theme === 'dark' ? 'text-indigo-400' : ''}`} />
              <span className="hidden sm:inline">Dark</span>
            </button>
          </div>
        </div>

      </div>
    </header>
  );
};
