import React, { useState, useMemo } from 'react';
import { 
  Plus, 
  Search, 
  Clock, 
  Calendar,
  PanelLeftClose, 
  BookOpen
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useReviews } from '../context/ReviewsContext';
import { StatusBadge } from './StatusBadge';
import type { ReviewOut } from '../types';

export const Sidebar: React.FC = () => {
  const { reviews, isLoading, sidebarOpen, setSidebarOpen } = useReviews();
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'recent'>('all');
  
  const navigate = useNavigate();
  const location = useLocation();

  // Determine current active review id from URL
  const currentReviewId = location.pathname.startsWith('/review/')
    ? decodeURIComponent(location.pathname.replace('/review/', ''))
    : null;

  // Filter reviews
  const filtered = useMemo(() => {
    let list = [...reviews];
    
    // Sort descending by created_at
    list.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    // If 'recent' tab, only show last 5 or within last 24h
    if (activeTab === 'recent') {
      const now = new Date().getTime();
      const oneDay = 24 * 60 * 60 * 1000;
      const recentList = list.filter((r) => now - new Date(r.created_at).getTime() < oneDay);
      list = recentList.length > 0 ? recentList : list.slice(0, 5);
    }

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      list = list.filter(
        (r) =>
          r.query.toLowerCase().includes(term) ||
          r.review_id.toLowerCase().includes(term)
      );
    }

    return list;
  }, [reviews, activeTab, searchTerm]);

  // Group by date categories: Today, Yesterday, Previous 7 Days, Older
  const grouped = useMemo(() => {
    const groups: { [key: string]: ReviewOut[] } = {
      Today: [],
      Yesterday: [],
      'Previous 7 Days': [],
      Older: [],
    };

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterday = today - 24 * 60 * 60 * 1000;
    const sevenDaysAgo = today - 7 * 24 * 60 * 60 * 1000;

    filtered.forEach((r) => {
      const time = new Date(r.created_at).getTime();
      if (time >= today) {
        groups.Today.push(r);
      } else if (time >= yesterday) {
        groups.Yesterday.push(r);
      } else if (time >= sevenDaysAgo) {
        groups['Previous 7 Days'].push(r);
      } else {
        groups.Older.push(r);
      }
    });

    return groups;
  }, [filtered]);

  const handleSelectReview = (id: string) => {
    navigate(`/review/${encodeURIComponent(id)}`);
    // Close sidebar on mobile
    if (window.innerWidth < 1024) {
      setSidebarOpen(false);
    }
  };

  const handleNewReview = () => {
    navigate('/');
    if (window.innerWidth < 1024) {
      setSidebarOpen(false);
    }
  };

  return (
    <>
      {/* Mobile backdrop overlay */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-xs z-30 lg:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-16 bottom-0 left-0 z-30 w-72 sm:w-80 bg-slate-50/95 dark:bg-slate-900/95 border-r border-slate-200 dark:border-slate-800 backdrop-blur-md flex flex-col transition-transform duration-300 ease-in-out shadow-lg lg:shadow-none ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full pointer-events-none'
        }`}
      >
        {/* Top Action Bar: New Review Button + Collapse button */}
        <div className="p-3 border-b border-slate-200/80 dark:border-slate-800/80 space-y-2.5">
          <div className="flex items-center gap-2">
            <button
              onClick={handleNewReview}
              className="flex-1 flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 shadow-sm shadow-indigo-600/20 transition cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>New Review</span>
            </button>

            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-slate-800 transition cursor-pointer border border-transparent hover:border-slate-200 dark:hover:border-slate-700"
              title="Collapse sidebar"
              aria-label="Collapse sidebar"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Filter Tabs: All / Recents */}
          <div className="flex items-center p-1 rounded-xl bg-slate-200/60 dark:bg-slate-800/60 text-xs">
            <button
              onClick={() => setActiveTab('all')}
              className={`flex-1 py-1 px-2 rounded-lg font-medium transition cursor-pointer text-center ${
                activeTab === 'all'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              All ({reviews.length})
            </button>
            <button
              onClick={() => setActiveTab('recent')}
              className={`flex-1 py-1 px-2 rounded-lg font-medium transition cursor-pointer flex items-center justify-center gap-1.5 ${
                activeTab === 'recent'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <Clock className="w-3 h-3" />
              <span>Recents</span>
            </button>
          </div>

          {/* Search bar inside history */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search history..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
        </div>

        {/* History Chat-style List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          {isLoading ? (
            <div className="space-y-2 py-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-12 bg-slate-200 dark:bg-slate-800 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-12 px-2 text-slate-400 space-y-2">
              <BookOpen className="w-8 h-8 mx-auto opacity-40" />
              <p className="text-xs font-medium">No reviews found</p>
              <p className="text-[11px] text-slate-400">
                {searchTerm ? 'Try a different search query' : 'Start a review to see it here'}
              </p>
            </div>
          ) : (
            Object.entries(grouped).map(([category, items]) => {
              if (items.length === 0) return null;
              return (
                <div key={category} className="space-y-1.5">
                  <div className="flex items-center gap-1.5 px-2 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                    <Calendar className="w-3 h-3" />
                    <span>{category}</span>
                  </div>

                  <div className="space-y-1">
                    {items.map((r) => {
                      const isSelected = r.review_id === currentReviewId;

                      return (
                        <button
                          key={r.review_id}
                          onClick={() => handleSelectReview(r.review_id)}
                          className={`w-full text-left p-2.5 rounded-xl border transition-all cursor-pointer group flex flex-col gap-1 ${
                            isSelected
                              ? 'bg-indigo-50 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-800/80 shadow-xs'
                              : 'bg-white/60 dark:bg-slate-950/40 border-transparent hover:bg-white dark:hover:bg-slate-800/60 hover:border-slate-200 dark:hover:border-slate-800'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-1 w-full">
                            <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500 truncate">
                              {r.review_id}
                            </span>
                            <StatusBadge status={r.status} showDot={false} />
                          </div>

                          <p
                            className={`text-xs font-medium line-clamp-2 leading-snug ${
                              isSelected
                                ? 'text-indigo-900 dark:text-indigo-200 font-semibold'
                                : 'text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-white'
                            }`}
                          >
                            {r.query}
                          </p>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
          <span>Literature Review Agent</span>
          <span className="font-mono">{reviews.length} total</span>
        </div>
      </aside>
    </>
  );
};
