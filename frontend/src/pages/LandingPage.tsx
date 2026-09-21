import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, ArrowUpRight, CheckCircle2, FileText, TrendingDown, TrendingUp } from 'lucide-react';
import { useInvoices } from '@/hooks/useInvoices';
import { SkeletonCard } from '@/components/common/Skeleton';

const formatAmount = (amount: number) =>
  amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  colorClass: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, icon, colorClass }) => (
  <div className="card p-5">
    <div className={`mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-bg-muted)] ${colorClass}`}>
      {icon}
    </div>
    <p className="text-2xl font-bold tabular-nums text-primary">{value}</p>
    <p className="mt-1 text-xs text-secondary">{label}</p>
  </div>
);

const DistributionBar: React.FC<{ label: string; value: number; total: number; color: string }> = ({
  label, value, total, color,
}) => (
  <div className="space-y-1.5">
    <div className="flex justify-between text-xs">
      <span className="text-secondary">{label}</span>
      <span className="font-medium text-primary">{value}</span>
    </div>
    <div className="h-2 rounded-full bg-[var(--color-bg-muted)]">
      <div className={`h-2 rounded-full ${color}`} style={{ width: `${total ? Math.max((value / total) * 100, 2) : 0}%` }} />
    </div>
  </div>
);

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading } = useInvoices({ limit: 100 });
  const invoices = data?.items ?? [];
  const extracted = invoices.filter(invoice => invoice.status === 'EXTRACTED');
  const incoming = extracted.filter(invoice => invoice.extracted_data?.direction !== 'OUTGOING');
  const outgoing = extracted.filter(invoice => invoice.extracted_data?.direction === 'OUTGOING');
  const incomingTotal = incoming.reduce((sum, invoice) => sum + (invoice.extracted_data?.total ?? 0), 0);
  const outgoingTotal = outgoing.reduce((sum, invoice) => sum + (invoice.extracted_data?.total ?? 0), 0);
  const processing = invoices.filter(invoice => ['PENDING', 'UPLOADED', 'OCR_COMPLETED'].includes(invoice.status)).length;
  const failed = invoices.filter(invoice => invoice.status === 'FAILED').length;

  return (
    <div className="animate-fade-in space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold text-primary">Overview</h1>
          <p className="mt-0.5 text-sm text-secondary">A financial snapshot of your processed invoices.</p>
        </div>
        <button onClick={() => navigate('/upload')} className="btn btn-primary">
          <FileText className="h-4 w-4" /> New Invoice
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{[1, 2, 3, 4].map(item => <SkeletonCard key={item} />)}</div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Total Invoices" value={data?.total ?? 0} icon={<FileText className="h-4 w-4" />} colorClass="text-brand-500" />
            <StatCard label="Incoming Total" value={formatAmount(incomingTotal)} icon={<TrendingDown className="h-4 w-4" />} colorClass="text-amber-500" />
            <StatCard label="Outgoing Total" value={formatAmount(outgoingTotal)} icon={<TrendingUp className="h-4 w-4" />} colorClass="text-emerald-500" />
            <StatCard label="Successfully Extracted" value={extracted.length} icon={<CheckCircle2 className="h-4 w-4" />} colorClass="text-blue-500" />
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <section className="card space-y-5 p-5">
              <div>
                <h2 className="text-sm font-semibold text-primary">Financial direction</h2>
                <p className="mt-1 text-xs text-secondary">Totals from extracted invoices (displayed in source currencies).</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg bg-[var(--color-bg-muted)] p-4">
                  <p className="text-xs text-secondary">Incoming · payable</p>
                  <p className="mt-2 text-lg font-bold text-primary">{formatAmount(incomingTotal)}</p>
                  <p className="mt-1 text-xs text-muted">{incoming.length} invoices</p>
                </div>
                <div className="rounded-lg bg-[var(--color-bg-muted)] p-4">
                  <p className="text-xs text-secondary">Outgoing · receivable</p>
                  <p className="mt-2 text-lg font-bold text-primary">{formatAmount(outgoingTotal)}</p>
                  <p className="mt-1 text-xs text-muted">{outgoing.length} invoices</p>
                </div>
              </div>
            </section>
            <section className="card space-y-4 p-5">
              <div>
                <h2 className="text-sm font-semibold text-primary">Processing distribution</h2>
                <p className="mt-1 text-xs text-secondary">Current lifecycle status across available invoices.</p>
              </div>
              <DistributionBar label="Extracted" value={extracted.length} total={invoices.length} color="bg-emerald-500" />
              <DistributionBar label="Processing" value={processing} total={invoices.length} color="bg-amber-500" />
              <DistributionBar label="Failed" value={failed} total={invoices.length} color="bg-red-500" />
            </section>
          </div>

          {invoices.length === 0 && (
            <div className="card p-8 text-center">
              <FileText className="mx-auto h-8 w-8 text-muted" />
              <h2 className="mt-3 text-sm font-semibold text-primary">No invoices yet</h2>
              <p className="mt-1 text-xs text-secondary">Upload an invoice to populate your financial overview.</p>
              <button onClick={() => navigate('/upload')} className="btn btn-primary btn-sm mt-4">Upload Invoice</button>
            </div>
          )}

          {(processing > 0 || failed > 0) && (
            <button onClick={() => navigate('/history')} className="card flex w-full items-center justify-between p-4 text-left hover:border-brand-500">
              <span className="flex items-center gap-2 text-sm text-secondary">
                <AlertCircle className="h-4 w-4 text-amber-500" /> Review {processing + failed} invoice{processing + failed === 1 ? '' : 's'} needing attention
              </span>
              <ArrowUpRight className="h-4 w-4 text-brand-500" />
            </button>
          )}
        </>
      )}
    </div>
  );
};
