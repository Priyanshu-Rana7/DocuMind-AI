import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const AppLayout: React.FC = () => {
  return (
    <div className="flex min-h-screen bg-[var(--color-bg-subtle)]">
      {/* Fixed Sidebar — Desktop */}
      <div className="hidden lg:block w-60 flex-shrink-0">
        <div className="fixed top-0 left-0 h-screen w-60 z-40">
          <Sidebar />
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        <Header />
        <main
          id="main-content"
          className="flex-1 px-4 py-6 sm:px-6 lg:px-8 max-w-screen-xl mx-auto w-full"
          tabIndex={-1}
          aria-label="Page content"
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
};
