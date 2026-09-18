import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Clock, CheckCircle2, AlertCircle, ArrowRight, TrendingUp, Zap, Shield } from 'lucide-react';
import { useInvoices } from '@/hooks/useInvoices';
import { StatusBadge } from '@/components/common/Badge';
import { SkeletonCard } from '@/components/common/Skeleton';
import { EmptyState } from '@/components/common/EmptyState';
import { Invoice } from '@/types/invoice';

/* ─── Stat Card ───────────────────────────────────────────── */
interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: string;
  colorClass?: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon, trend, colorClass = 'text-brand-500' }) => (
  <div className="card p-5">
    <div className="flex items-start justify-between mb-3">
      <div className={`flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--color-bg-muted)] ${colorClass}`}>
        {icon}
      </div>
      {trend && (
        <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-0.5">
          <TrendingUp className="h-3 w-3" /> {trend}
        </span>
      )}
    </div>
    <p className="text-2xl font-bold text-primary tabular-nums">{value}</p>
    <p className="text-xs text-secondary mt-1">{label}</p>
  </div>
);

/* ─── Recent Invoice Row ─────────────────────────────────── */
const RecentRow: React.FC<{ invoice: Invoice; onClick: () => void }> = ({ invoice, onClick }) => {
  const date = new Date(invoice.created_at).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });
  const total = invoice.extracted_data?.total;

  return (
    <tr
      onClick={onClick}
      className="cursor-pointer"
      role="row"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onClick()}
      aria-label={`View invoice ${invoice.filename}`}
    >
      <td className="px-4 py-3.5 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center justify-center w-7 h-7 rounded-md bg-[var(--color-bg-muted)] flex-shrink-0">
            <FileText className="h-3.5 w-3.5 text-secondary" />
          </div>
          <span className="text-sm font-medium text-primary truncate-text max-w-[200px]">
            {invoice.filename}
          </span>
        </div>
      </td>
      <td className="px-4 py-3.5 border-b border-[var(--color-border)] text-sm text-secondary">
        {invoice.extracted_data?.vendor_name ?? <span className="text-muted">—</span>}
      </td>
      <td className="px-4 py-3.5 border-b border-[var(--color-border)] text-sm text-secondary whitespace-nowrap">
        {date}
      </td>
      <td className="px-4 py-3.5 border-b border-[var(--color-border)]">
        <StatusBadge status={invoice.status} />
      </td>
      <td className="px-4 py-3.5 border-b border-[var(--color-border)] text-sm font-medium text-primary text-right whitespace-nowrap">
        {total != null
          ? `${invoice.extracted_data?.currency ?? 'USD'} ${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
          : <span className="text-muted">—</span>}
      </td>
    </tr>
  );
};

/* ─── Landing/Overview Page ──────────────────────────────── */
export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading } = useInvoices({ limit: 5 });

  const invoices = data?.items ?? [];
  const total    = data?.total ?? 0;

  const extracted = invoices.filter(i => i.status === 'EXTRACTED').length;
  const failed    = invoices.filter(i => i.status === 'FAILED').length;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-primary">Overview</h1>
          <p className="text-sm text-secondary mt-0.5">
            Welcome back — your AI-powered invoice intelligence hub.
          </p>
        </div>
        <button
          onClick={() => navigate('/upload')}
          className="btn btn-primary"
          aria-label="Upload a new invoice"
        >
          <FileText className="h-4 w-4" />
          New Invoice
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Processed"
          value={isLoading ? '—' : total}
          icon={<FileText className="h-4.5 w-4.5" />}
          colorClass="text-brand-500"
        />
        <StatCard
          label="Extracted Successfully"
          value={isLoading ? '—' : extracted}
          icon={<CheckCircle2 className="h-4.5 w-4.5" />}
          colorClass="text-emerald-500"
        />
        <StatCard
          label="Processing"
          value={isLoading ? '—' : invoices.filter(i => i.status === 'OCR_COMPLETED').length}
          icon={<Clock className="h-4.5 w-4.5" />}
          colorClass="text-amber-500"
        />
        <StatCard
          label="Failed"
          value={isLoading ? '—' : failed}
          icon={<AlertCircle className="h-4.5 w-4.5" />}
          colorClass="text-red-500"
        />
      </div>

      {/* Feature Highlights — useful until first invoice */}
      {total === 0 && !isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: <Zap className="h-5 w-5" />, title: 'OCR Text Extraction', desc: 'Multi-page PDFs and scanned images processed with high accuracy.', color: 'text-brand-500' },
            { icon: <CheckCircle2 className="h-5 w-5" />, title: 'AI-Structured Output', desc: 'Vendor, customer, line items, totals, and payment terms — extracted automatically.', color: 'text-emerald-500' },
            { icon: <Shield className="h-5 w-5" />, title: 'Export Ready', desc: 'Download extracted data as CSV, Excel, or raw JSON instantly.', color: 'text-amber-500' },
          ].map(f => (
            <div key={f.title} className="card p-5 space-y-2.5">
              <div className={`${f.color} bg-[var(--color-bg-muted)] w-9 h-9 rounded-lg flex items-center justify-center`}>
                {f.icon}
              </div>
              <h3 className="text-sm font-semibold text-primary">{f.title}</h3>
              <p className="text-xs text-secondary leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      )}

      {/* Recent Invoices Table */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--color-border)]">
          <h2 className="text-sm font-semibold text-primary">Recent Invoices</h2>
          {total > 5 && (
            <button
              onClick={() => navigate('/history')}
              className="btn btn-ghost btn-sm flex items-center gap-1 text-brand-500"
            >
              View all <ArrowRight className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        {isLoading ? (
          <div className="p-5 grid gap-3">
            {[0, 1, 2].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : invoices.length === 0 ? (
          <EmptyState
            icon={<FileText className="h-6 w-6" />}
            title="No invoices yet"
            description="Upload your first invoice to get started with AI-powered extraction."
            action={
              <button onClick={() => navigate('/upload')} className="btn btn-primary btn-sm">
                Upload Invoice
              </button>
            }
          />
        ) : (
          <div className="table-wrapper">
            <table className="data-table" role="table" aria-label="Recent invoices">
              <thead>
                <tr role="row">
                  <th role="columnheader">Document</th>
                  <th role="columnheader">Vendor</th>
                  <th role="columnheader">Date</th>
                  <th role="columnheader">Status</th>
                  <th role="columnheader" className="text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map(inv => (
                  <RecentRow
                    key={inv.id}
                    invoice={inv}
                    onClick={() => navigate(`/invoices/${inv.id}`)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
