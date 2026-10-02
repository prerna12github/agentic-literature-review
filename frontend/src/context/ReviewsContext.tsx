import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { listReviews } from '../api';
import type { ReviewOut } from '../types';

interface ReviewsContextType {
  reviews: ReviewOut[];
  isLoading: boolean;
  refreshReviews: () => Promise<void>;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
}

const ReviewsContext = createContext<ReviewsContextType>({
  reviews: [],
  isLoading: false,
  refreshReviews: async () => {},
  sidebarOpen: true,
  setSidebarOpen: () => {},
  toggleSidebar: () => {},
});

export const ReviewsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [reviews, setReviews] = useState<ReviewOut[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('sidebar_open');
      if (saved !== null) {
        return saved === 'true';
      }
      return window.innerWidth >= 1024;
    }
    return true;
  });

  const refreshReviews = useCallback(async () => {
    try {
      const data = await listReviews();
      setReviews(data);
    } catch {
      // ignore or let caller handle
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshReviews();
  }, [refreshReviews]);

  const updateSidebarOpen = (open: boolean) => {
    setSidebarOpen(open);
    try {
      localStorage.setItem('sidebar_open', String(open));
    } catch {
      // ignore
    }
  };

  const toggleSidebar = () => {
    setSidebarOpen((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('sidebar_open', String(next));
      } catch {
        // ignore
      }
      return next;
    });
  };

  return (
    <ReviewsContext.Provider
      value={{
        reviews,
        isLoading,
        refreshReviews,
        sidebarOpen,
        setSidebarOpen: updateSidebarOpen,
        toggleSidebar,
      }}
    >
      {children}
    </ReviewsContext.Provider>
  );
};

export const useReviews = () => useContext(ReviewsContext);
