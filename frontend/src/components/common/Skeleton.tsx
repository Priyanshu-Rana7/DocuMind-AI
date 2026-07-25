import React from 'react';
import clsx from 'clsx';

interface SkeletonProps {
  className?: string;
  width?: string;
  height?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, width, height }) => (
  <div
    className={clsx('skeleton', className)}
    style={{ width, height }}
    aria-hidden="true"
  />
);

export const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({
  lines = 3,
  className,
}) => (
  <div className={clsx('space-y-2', className)} aria-hidden="true">
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        height="14px"
        width={i === lines - 1 ? '60%' : '100%'}
      />
    ))}
  </div>
);

export const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={clsx('card p-5 space-y-4', className)} aria-hidden="true">
    <div className="flex items-center gap-3">
      <Skeleton className="rounded-lg" width="36px" height="36px" />
      <div className="flex-1 space-y-2">
        <Skeleton height="14px" width="40%" />
        <Skeleton height="12px" width="60%" />
      </div>
    </div>
    <SkeletonText lines={3} />
  </div>
);

export const SkeletonTableRow: React.FC<{ cols?: number }> = ({ cols = 5 }) => (
  <tr aria-hidden="true">
    {Array.from({ length: cols }).map((_, i) => (
      <td key={i} className="px-4 py-3 border-b border-[var(--color-border)]">
        <Skeleton height="14px" width={i === 0 ? '70%' : '50%'} />
      </td>
    ))}
  </tr>
);
