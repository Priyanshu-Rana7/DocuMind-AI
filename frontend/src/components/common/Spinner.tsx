import React from 'react';
import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
}

const sizes = { sm: 'h-4 w-4', md: 'h-5 w-5', lg: 'h-7 w-7' };

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  className,
  label = 'Loading…',
}) => (
  <span role="status" aria-label={label} className="inline-flex items-center justify-center">
    <Loader2 className={clsx('animate-spin text-[var(--color-brand-500)]', sizes[size], className)} />
    <span className="sr-only">{label}</span>
  </span>
);

/* --- Full-page centered spinner --- */
export const PageSpinner: React.FC<{ label?: string }> = ({ label = 'Loading…' }) => (
  <div className="flex flex-col items-center justify-center py-24 gap-3" role="status">
    <Spinner size="lg" />
    <p className="text-sm text-secondary animate-pulse-soft">{label}</p>
  </div>
);

/* --- Inline processing step indicator --- */
interface ProcessingStepProps {
  steps: Array<{ label: string; done: boolean; active: boolean }>;
}

export const ProcessingSteps: React.FC<ProcessingStepProps> = ({ steps }) => (
  <div className="flex flex-col gap-2.5" role="list" aria-label="Processing steps">
    {steps.map((step, i) => (
      <div
        key={i}
        className="flex items-center gap-3 text-sm"
        role="listitem"
        aria-current={step.active ? 'step' : undefined}
      >
        <span
          className={clsx(
            'flex items-center justify-center w-5 h-5 rounded-full text-xs font-bold flex-shrink-0 transition-all duration-300',
            step.done   ? 'bg-emerald-500 text-white'          : '',
            step.active ? 'bg-brand-500 text-white animate-pulse-soft' : '',
            !step.done && !step.active ? 'bg-[var(--color-bg-muted)] text-muted' : '',
          )}
        >
          {step.done ? '✓' : i + 1}
        </span>
        <span className={clsx(
          'transition-colors duration-200',
          step.done   ? 'text-primary'    : '',
          step.active ? 'text-primary font-medium' : '',
          !step.done && !step.active ? 'text-muted' : '',
        )}>
          {step.label}
        </span>
        {step.active && <Spinner size="sm" className="ml-auto" />}
      </div>
    ))}
  </div>
);
