import React from 'react';
import clsx from 'clsx';

interface ConfidenceMeterProps {
  value: number; // 0–1 float
  showLabel?: boolean;
  className?: string;
}

const getColor = (v: number) => {
  if (v >= 0.85) return { fill: 'bg-emerald-500', text: 'text-emerald-600 dark:text-emerald-400' };
  if (v >= 0.65) return { fill: 'bg-amber-500',   text: 'text-amber-600 dark:text-amber-400' };
  return           { fill: 'bg-red-500',    text: 'text-red-600 dark:text-red-400' };
};

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  value,
  showLabel = true,
  className,
}) => {
  const pct = Math.round(Math.min(Math.max(value, 0), 1) * 100);
  const { fill, text } = getColor(value);

  return (
    <div className={clsx('flex items-center gap-2.5', className)}>
      <div className="confidence-bar flex-1" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className={clsx('confidence-bar-fill', fill)} style={{ width: `${pct}%` }} />
      </div>
      {showLabel && (
        <span className={clsx('text-xs font-semibold tabular-nums w-8 text-right', text)}>
          {pct}%
        </span>
      )}
    </div>
  );
};
