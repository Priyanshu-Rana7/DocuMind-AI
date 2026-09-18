import React from 'react';
import { Cpu, Database, Palette, Code2, ChevronRight } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { invoiceApi } from '@/api/invoiceApi';
import { Badge } from '@/components/common/Badge';
import { Skeleton } from '@/components/common/Skeleton';

interface SettingRowProps {
  label: string;
  value: string;
  description?: string;
  badge?: string;
}

const SettingRow: React.FC<SettingRowProps> = ({ label, value, description, badge }) => (
  <div className="flex items-center gap-4 py-3.5 border-b border-[var(--color-border)] last:border-0">
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm font-medium text-primary">{label}</span>
        {badge && <Badge variant="brand" className="text-[10px]">{badge}</Badge>}
      </div>
      {description && <p className="text-xs text-secondary mt-0.5">{description}</p>}
    </div>
    <span className="text-xs font-mono text-secondary bg-[var(--color-bg-muted)] px-2 py-1 rounded-md flex-shrink-0">
      {value}
    </span>
  </div>
);

interface SectionProps {
  icon: React.ReactNode;
  title: string;
  description?: string;
  children: React.ReactNode;
}

const SettingsSection: React.FC<SectionProps> = ({ icon, title, description, children }) => (
  <div className="card overflow-hidden">
    <div className="flex items-center gap-3 px-5 py-4 border-b border-[var(--color-border)] bg-[var(--color-bg-subtle)]">
      <div className="w-8 h-8 rounded-lg bg-brand-50 dark:bg-[color-mix(in_srgb,var(--color-brand-500)_12%,transparent)] flex items-center justify-center text-brand-600 dark:text-brand-400 flex-shrink-0">
        {icon}
      </div>
      <div>
        <h2 className="text-sm font-semibold text-primary">{title}</h2>
        {description && <p className="text-xs text-muted">{description}</p>}
      </div>
    </div>
    <div className="px-5 py-1">{children}</div>
  </div>
);

export const SettingsPage: React.FC = () => {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: invoiceApi.getHealth,
    staleTime: 30_000,
  });

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-primary">Settings</h1>
        <p className="text-sm text-secondary mt-0.5">
          System configuration. Edit values via the <code className="text-xs bg-[var(--color-bg-muted)] px-1 py-0.5 rounded">.env</code> file in the backend directory.
        </p>
      </div>

      {/* System Status */}
      <SettingsSection
        icon={<Database className="h-4 w-4" />}
        title="System Status"
        description="Live health check against the API backend."
      >
        {isLoading ? (
          <div className="py-3 space-y-3">
            {[0, 1, 2].map(i => <Skeleton key={i} height="28px" />)}
          </div>
        ) : health ? (
          <>
            <SettingRow label="API Status"   value={health.status}      badge={health.status === 'ok' ? 'Healthy' : 'Degraded'} />
            <SettingRow label="Database"     value={health.database}    description="Connection pool status" />
            <SettingRow
              label="Database Schema"
              value={health.migration}
              description="Alembic migration revision applied to the active database"
              badge={health.migration !== 'not_initialized' ? 'Migrated' : 'Needs migration'}
            />
            <SettingRow label="Environment"  value={health.environment} />
            <SettingRow label="Version"      value={health.version} />
          </>
        ) : (
          <div className="py-4 text-sm text-secondary text-center">Failed to load system status.</div>
        )}
      </SettingsSection>

      {/* AI / LLM Config */}
      <SettingsSection
        icon={<Cpu className="h-4 w-4" />}
        title="AI / LLM Provider"
        description="Configure via OPENROUTER_* environment variables."
      >
        {isLoading ? (
          <div className="py-3 space-y-3">
            {[0, 1].map(i => <Skeleton key={i} height="28px" />)}
          </div>
        ) : (
          <>
            <SettingRow
              label="Provider"
              value={health?.llm_provider ?? '—'}
              description="LLM backend used for structured invoice parsing"
            />
            <SettingRow
              label="Configuration"
              value={health?.llm_configured ? 'Ready' : 'Not configured'}
              description="API credentials are checked on the backend and never exposed here"
              badge={health?.llm_configured ? 'Ready' : 'Action needed'}
            />
            <SettingRow
              label="Model"
              value={health?.llm_model ?? '—'}
              description="Set via OPENROUTER_MODEL environment variable"
            />
          </>
        )}
      </SettingsSection>

      {/* OCR Config */}
      <SettingsSection
        icon={<Code2 className="h-4 w-4" />}
        title="OCR Engine"
        description="Configure via OCR_PROVIDER environment variable."
      >
        {isLoading ? (
          <div className="py-3"><Skeleton height="28px" /></div>
        ) : (
          <>
            <SettingRow
              label="Provider"
              value={health?.ocr_provider ?? '—'}
              description="Active OCR engine for text recognition"
            />
            <SettingRow
              label="Configuration"
              value={health?.ocr_configured ? 'Ready' : 'Not configured'}
              description="OCR provider selection is validated without exposing local dependencies"
              badge={health?.ocr_configured ? 'Ready' : 'Action needed'}
            />
            <SettingRow
              label="PDF support"
              value={health?.poppler_configured ? 'Configured' : 'PATH lookup'}
              description="Poppler is used to convert PDF pages before OCR"
            />
          </>
        )}
      </SettingsSection>

      {/* Appearance */}
      <SettingsSection
        icon={<Palette className="h-4 w-4" />}
        title="Appearance"
        description="Theme preference is stored locally in your browser."
      >
        <SettingRow
          label="Theme"
          value="System / Manual Toggle"
          description="Use the sun/moon button in the top-right header to switch modes"
        />
      </SettingsSection>

      {/* Info Banner */}
      <div className="flex items-start gap-3 px-4 py-3.5 rounded-xl bg-[var(--color-bg-muted)] border border-[var(--color-border)]">
        <ChevronRight className="h-4 w-4 text-brand-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-xs font-semibold text-primary">Editing Configuration</p>
          <p className="text-xs text-secondary mt-0.5 leading-relaxed">
            All settings are managed via environment variables in the backend <code className="bg-[var(--color-border)] px-1 rounded">.env</code> file.
            No secrets are stored in the database or transmitted to the frontend.
          </p>
        </div>
      </div>
    </div>
  );
};
