import React from 'react';
import clsx from 'clsx';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => (
  <div
    className={clsx(
      'flex flex-col items-center justify-center text-center py-16 px-8',
      className
    )}
    role="status"
    aria-label={title}
  >
    <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-[var(--color-bg-muted)] text-[var(--color-text-muted)] mb-4">
      {icon}
    </div>
    <h3 className="text-base font-semibold text-primary mb-1.5">{title}</h3>
    {description && (
      <p className="text-sm text-secondary max-w-xs leading-relaxed">{description}</p>
    )}
    {action && <div className="mt-5">{action}</div>}
  </div>
);

/* --- Error State --- */
interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onRetry,
  className,
}) => (
  <div className={clsx('flex flex-col items-center justify-center text-center py-16 px-8', className)}>
    <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-[var(--color-error-bg)] text-red-500 mb-4">
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      </svg>
    </div>
    <h3 className="text-base font-semibold text-primary mb-1.5">{title}</h3>
    <p className="text-sm text-secondary max-w-xs leading-relaxed">{message}</p>
    {onRetry && (
      <button onClick={onRetry} className="btn btn-secondary btn-sm mt-5">
        Try Again
      </button>
    )}
  </div>
);
