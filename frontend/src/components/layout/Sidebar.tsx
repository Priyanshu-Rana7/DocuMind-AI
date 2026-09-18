import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Upload, History, Settings, Sparkles, FileSearch, LayoutDashboard } from 'lucide-react';
import clsx from 'clsx';

interface NavItem {
  to: string;
  label: string;
  icon: React.FC<{ className?: string }>;
  badge?: string;
}

const PRIMARY_NAV: NavItem[] = [
  { to: '/',        label: 'Overview',       icon: LayoutDashboard },
  { to: '/upload',  label: 'Upload Invoice', icon: Upload },
  { to: '/history', label: 'Invoice History', icon: History },
];

const SECONDARY_NAV: NavItem[] = [
  { to: '/settings', label: 'Settings', icon: Settings },
];

// Future modules — demonstrates design extensibility
const FUTURE_MODULES = [
  { label: 'Contract Analysis', icon: FileSearch, coming: true },
];

interface SidebarProps {
  onNavigate?: () => void; // for mobile drawer close
}

export const Sidebar: React.FC<SidebarProps> = ({ onNavigate }) => {
  return (
    <aside className="sidebar flex flex-col h-full min-h-screen" aria-label="Main navigation">
      {/* Brand */}
      <Link
        to="/"
        className="flex items-center gap-3 px-5 py-5 border-b border-[var(--color-border)] hover:bg-[var(--color-bg-muted)] transition-colors"
        onClick={onNavigate}
        aria-label="DocuMind AI Home"
      >
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-600 shadow-sm flex-shrink-0">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <div className="leading-none">
          <span className="text-[15px] font-bold text-primary tracking-tight">DocuMind</span>
          <span className="text-[15px] font-bold text-brand-500 tracking-tight"> AI</span>
        </div>
      </Link>

      {/* Primary Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5" aria-label="Primary navigation">
        <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-muted">
          Document Processing
        </p>
        {PRIMARY_NAV.map(({ to, label, icon: Icon, badge }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            onClick={onNavigate}
            className={({ isActive }) =>
              clsx('nav-item', isActive && 'active')
            }
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            <span className="flex-1 truncate">{label}</span>
            {badge && (
              <span className="badge badge-brand text-[10px] px-1.5 py-0.5">{badge}</span>
            )}
          </NavLink>
        ))}

        {/* Future Modules Section */}
        <div className="pt-4">
          <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-muted">
            Coming Soon
          </p>
          {FUTURE_MODULES.map(({ label, icon: Icon }) => (
            <div
              key={label}
              className="nav-item opacity-50 cursor-not-allowed select-none"
              aria-disabled="true"
              title="Coming soon"
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span className="flex-1 truncate">{label}</span>
              <span className="badge badge-neutral text-[10px]">Soon</span>
            </div>
          ))}
        </div>
      </nav>

      {/* Secondary Nav / Footer */}
      <div className="px-3 py-3 border-t border-[var(--color-border)] space-y-0.5">
        {SECONDARY_NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className={({ isActive }) => clsx('nav-item', isActive && 'active')}
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            <span className="flex-1 truncate">{label}</span>
          </NavLink>
        ))}
      </div>
    </aside>
  );
};
