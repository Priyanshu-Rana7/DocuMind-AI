import React from 'react';
import clsx from 'clsx';
import { InvoiceStatus } from '@/types/invoice';

const statusConfig: Record<
  InvoiceStatus,
  { label: string; className: string; dot: string }
> = {
  PENDING:       { label: 'Pending',        className: 'badge-neutral', dot: 'bg-gray-400' },
  UPLOADED:      { label: 'Uploaded',       className: 'badge-info',    dot: 'bg-blue-500' },
  OCR_COMPLETED: { label: 'OCR Done',       className: 'badge-warning', dot: 'bg-amber-500' },
  EXTRACTED:     { label: 'Extracted',      className: 'badge-success', dot: 'bg-emerald-500' },
  FAILED:        { label: 'Failed',         className: 'badge-error',   dot: 'bg-red-500' },
};

interface StatusBadgeProps {
  status: InvoiceStatus;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const config = statusConfig[status] ?? statusConfig.PENDING;
  return (
    <span className={clsx('badge', config.className, className)}>
      <span className={clsx('inline-block w-1.5 h-1.5 rounded-full', config.dot)} />
      {config.label}
    </span>
  );
};

/* --- Generic Badge --- */
interface BadgeProps {
  variant?: 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'brand';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'neutral', children, className }) => (
  <span className={clsx('badge', `badge-${variant}`, className)}>
    {children}
  </span>
);
