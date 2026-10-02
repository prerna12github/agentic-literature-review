import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { ReviewsProvider, useReviews } from './context/ReviewsContext';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { HomePage } from './pages/HomePage';
import { ReviewDetailPage } from './pages/ReviewDetailPage';

function AppContent() {
  const { sidebarOpen } = useReviews();

  return (
    <div className="min-h-screen flex flex-col transition-colors duration-200 bg-[#f8fafc] dark:bg-[#090d16]">
      <Header />
      <div className="flex-1 flex relative">
        <Sidebar />
        <main
          className={`flex-1 min-w-0 transition-all duration-300 ease-in-out ${
            sidebarOpen ? 'lg:pl-80' : 'lg:pl-0'
          }`}
        >
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/review/:id" element={<ReviewDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <BrowserRouter>
          <ReviewsProvider>
            <AppContent />
          </ReviewsProvider>
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
