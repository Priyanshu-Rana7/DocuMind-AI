import React from 'react';
import { useLocation } from 'react-router-dom';
import { Sun, Moon, Bell, Search, ChevronRight } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';

const routeTitles: Record<string, { title: string; breadcrumb?: string }> = {
  '/':          { title: 'Overview' },
  '/upload':    { title: 'Upload Invoice', breadcrumb: 'New Document' },
  '/history':   { title: 'Invoice History', breadcrumb: 'All Documents' },
  '/settings':  { title: 'Settings', breadcrumb: 'Preferences' },
};

export const Header: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { pathname } = useLocation();

  // Resolve route (handle dynamic routes like /invoices/:id)
  const routeKey = Object.keys(routeTitles)
    .sort((a, b) => b.length - a.length)
    .find(key => pathname === key || pathname.startsWith(key + '/')) ?? '/';
  const { title, breadcrumb } = routeTitles[routeKey] ?? { title: 'DocuMind AI' };

  return (
    <header
      className="sticky top-0 z-30 flex items-center gap-4 h-14 px-6 border-b border-[var(--color-border)] bg-[var(--color-bg-base)]"
      role="banner"
    >
      {/* Breadcrumb */}
      <div className="flex items-center gap-1.5 flex-1 min-w-0 mr-4">
        <span className="text-sm font-semibold text-primary truncate">{title}</span>
        {breadcrumb && (
          <>
            <ChevronRight className="h-3.5 w-3.5 text-muted flex-shrink-0" />
            <span className="text-sm text-secondary truncate">{breadcrumb}</span>
          </>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="btn btn-ghost btn-sm w-8 h-8 p-0"
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark'
            ? <Sun className="h-4 w-4" />
            : <Moon className="h-4 w-4" />
          }
        </button>

        {/* Divider */}
        <div className="w-px h-4 bg-[var(--color-border)] mx-1" aria-hidden="true" />

        {/* User Avatar placeholder */}
        <div
          className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-white text-xs font-bold"
          aria-label="User account"
          title="User account"
        >
          DM
        </div>
      </div>
    </header>
  );
};
