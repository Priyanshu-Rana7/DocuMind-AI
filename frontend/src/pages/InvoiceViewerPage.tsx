import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, FileText, Building2, User, Calendar, CreditCard, Tag } from 'lucide-react';
import { useInvoice } from '@/hooks/useInvoices';
import { StatusBadge } from '@/components/common/Badge';
import { ConfidenceMeter } from '@/components/common/ConfidenceMeter';
import { PageSpinner } from '@/components/common/Spinner';
import { ErrorState } from '@/components/common/EmptyState';
import { Skeleton } from '@/components/common/Skeleton';
import type { ExtractedInvoiceData, InvoiceItem } from '@/types/invoice';

/* ─── Detail Field ──────────────────────────────────────── */
interface FieldProps {
  label: string;
  value?: string | number | null;
  icon?: React.ReactNode;
  mono?: boolean;
}

const Field: React.FC<FieldProps> = ({ label, value, icon, mono }) => (
  <div className="space-y-1">
    <div className="flex items-center gap-1.5">
      {icon && <span className="text-muted">{icon}</span>}
      <dt className="text-[11px] font-semibold uppercase tracking-wide text-muted">{label}</dt>
    </div>
    <dd className={`text-sm text-primary ${mono ? 'font-mono' : ''}`}>
      {value != null && value !== '' ? String(value) : <span className="text-muted">—</span>}
    </dd>
  </div>
);

/* ─── Amount Field ─────────────────────────────────────── */
const AmountField: React.FC<{ label: string; value: number; currency: string; highlight?: boolean }> = ({
  label, value, currency, highlight,
}) => (
  <div className={`flex items-center justify-between py-2.5 ${highlight ? 'border-t border-[var(--color-border)] mt-1 pt-3' : ''}`}>
    <span className={`text-sm ${highlight ? 'font-semibold text-primary' : 'text-secondary'}`}>{label}</span>
    <span className={`tabular-nums ${highlight ? 'text-base font-bold text-primary' : 'text-sm text-primary'}`}>
      {currency} {value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
    </span>
  </div>
);

/* ─── Line Items Table ─────────────────────────────────── */
const LineItemsTable: React.FC<{ items: InvoiceItem[]; currency: string }> = ({ items, currency }) => (
  <div className="table-wrapper rounded-lg border border-[var(--color-border)] overflow-hidden">
    <table className="data-table" aria-label="Invoice line items">
      <thead>
        <tr>
          <th>Description</th>
          <th className="text-right">Qty</th>
          <th className="text-right">Unit Price</th>
          <th className="text-right">Total</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item, i) => (
          <tr key={i}>
            <td className="text-primary font-medium">{item.description}</td>
            <td className="text-right tabular-nums">{item.quantity}</td>
            <td className="text-right tabular-nums">
              {currency} {item.unit_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </td>
            <td className="text-right tabular-nums font-medium text-primary">
              {currency} {item.total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

/* ─── Invoice Viewer Page ───────────────────────────────── */
export const InvoiceViewerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: invoice, isLoading, isError, error } = useInvoice(id);

  if (isLoading) return <PageSpinner label="Loading invoice details…" />;
  if (isError || !invoice) {
    return (
      <ErrorState
        title="Invoice not found"
        message={error instanceof Error ? error.message : 'This invoice could not be loaded.'}
        onRetry={() => navigate('/history')}
      />
    );
  }

  const data: ExtractedInvoiceData | undefined = invoice.extracted_data;
  const currency = data?.currency ?? 'USD';

  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url;
    a.download = `${invoice.filename.replace(/\.[^.]+$/, '')}_extracted.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:justify-between">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => navigate('/history')}
            className="btn btn-ghost btn-sm p-2 flex-shrink-0"
            aria-label="Back to history"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div className="min-w-0">
            <h1 className="text-lg font-bold text-primary truncate">{invoice.filename}</h1>
            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
              <StatusBadge status={invoice.status} />
              <span className="text-xs text-muted">
                {new Date(invoice.created_at).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button onClick={downloadJSON} className="btn btn-secondary btn-sm" disabled={!data}>
            <Download className="h-3.5 w-3.5" /> JSON
          </button>
        </div>
      </div>

      {/* Confidence Meter */}
      {invoice.overall_confidence != null && (
        <div className="card p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-secondary">AI Extraction Confidence</span>
            <span className="text-xs text-muted">
              {invoice.extracted_data?.invoice_number
                ? `Invoice #${invoice.extracted_data.invoice_number}`
                : 'Unidentified'}
            </span>
          </div>
          <ConfidenceMeter value={invoice.overall_confidence} />
        </div>
      )}

      {/* Extracted Data Grid */}
      {data ? (
        <div className="space-y-5">
          {/* Vendor & Customer */}
          <div className="card p-5 grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="space-y-4">
              <h2 className="text-xs font-semibold uppercase tracking-widest text-muted">Vendor</h2>
              <Field label="Company"  value={data.vendor_name}    icon={<Building2 className="h-3.5 w-3.5" />} />
              <Field label="Address"  value={data.vendor_address} />
            </div>
            <div className="space-y-4">
              <h2 className="text-xs font-semibold uppercase tracking-widest text-muted">Bill To</h2>
              <Field label="Customer" value={data.customer_name} icon={<User className="h-3.5 w-3.5" />} />
              <Field label="Payment Terms" value={data.payment_terms} icon={<CreditCard className="h-3.5 w-3.5" />} />
            </div>
          </div>

          {/* Invoice Meta */}
          <div className="card p-5 grid grid-cols-2 sm:grid-cols-4 gap-5">
            <Field label="Invoice #"     value={data.invoice_number} icon={<Tag className="h-3.5 w-3.5" />} mono />
            <Field label="Invoice Date"  value={data.invoice_date}   icon={<Calendar className="h-3.5 w-3.5" />} />
            <Field label="Due Date"      value={data.due_date}       icon={<Calendar className="h-3.5 w-3.5" />} />
            <Field label="Currency"      value={data.currency} />
          </div>

          {/* Line Items */}
          {data.invoice_items && data.invoice_items.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-primary">Line Items</h2>
              <LineItemsTable items={data.invoice_items} currency={currency} />
            </div>
          )}

          {/* Totals */}
          <div className="card p-5 max-w-xs ml-auto">
            <AmountField label="Subtotal" value={data.subtotal}  currency={currency} />
            {data.tax      > 0 && <AmountField label="Tax"      value={data.tax}      currency={currency} />}
            {data.discount > 0 && <AmountField label="Discount" value={-data.discount} currency={currency} />}
            <AmountField label="Total Due" value={data.total} currency={currency} highlight />
          </div>
        </div>
      ) : (
        /* Not yet extracted */
        <div className="card p-10 flex flex-col items-center text-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-[var(--color-bg-muted)] flex items-center justify-center">
            <FileText className="h-6 w-6 text-muted" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-primary">Not yet extracted</h3>
            <p className="text-sm text-secondary mt-1">This invoice has been uploaded but not processed yet.</p>
          </div>
        </div>
      )}
    </div>
  );
};
