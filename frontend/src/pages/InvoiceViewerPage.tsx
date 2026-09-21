import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertTriangle, ArrowLeft, CheckCircle2, Download, FileText, Building2, User, Calendar, CreditCard, Tag, ChevronDown, FileSpreadsheet, Table2 } from 'lucide-react';
import { useCorrectInvoice, useExtractInvoice, useInvoice, useRetryInvoice } from '@/hooks/useInvoices';
import { StatusBadge } from '@/components/common/Badge';
import { ConfidenceMeter } from '@/components/common/ConfidenceMeter';
import { PageSpinner, Spinner } from '@/components/common/Spinner';
import { ErrorState } from '@/components/common/EmptyState';
import { invoiceApi } from '@/api/invoiceApi';
import { useToast } from '@/context/ToastContext';
import type { ExtractedInvoiceData, InvoiceItem, InvoiceStatus } from '@/types/invoice';

/* ─── Export Dropdown ───────────────────────────────────── */
const ExportDropdown: React.FC<{
  invoiceId: string;
  disabled: boolean;
  invoice?: ReturnType<typeof useInvoice>['data'];
}> = ({ invoiceId, disabled, invoice }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<'csv' | 'xlsx' | null>(null);
  const { toast } = useToast();
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleExport = async (format: 'csv' | 'xlsx') => {
    setOpen(false);
    setLoading(format);
    try {
      await invoiceApi.exportInvoice(invoiceId, format);
      toast.success(`${format.toUpperCase()} downloaded`, 'Your invoice data has been exported.');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Export failed.';
      toast.error('Export failed', msg);
    } finally {
      setLoading(null);
    }
  };

  const isLoading = loading !== null;

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(v => !v)}
        disabled={disabled || isLoading}
        className="btn btn-secondary btn-sm flex items-center gap-1.5"
        aria-haspopup="true"
        aria-expanded={open}
        aria-label="Export invoice data"
      >
        {isLoading ? <Spinner size="sm" /> : <Download className="h-3.5 w-3.5" />}
        Export
        <ChevronDown className={`h-3 w-3 transition-transform duration-150 ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-1.5 w-48 card py-1 z-50 animate-slide-down"
          role="menu"
          aria-label="Export options"
        >
          <button
            onClick={() => handleExport('csv')}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-secondary hover:bg-[var(--color-bg-muted)] hover:text-primary transition-colors"
            role="menuitem"
          >
            <Table2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
            <div className="text-left">
              <p className="font-medium text-primary">CSV</p>
              <p className="text-xs text-muted">Comma-separated values</p>
            </div>
          </button>
          <button
            onClick={() => handleExport('xlsx')}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-secondary hover:bg-[var(--color-bg-muted)] hover:text-primary transition-colors"
            role="menuitem"
          >
            <FileSpreadsheet className="h-4 w-4 text-blue-500 flex-shrink-0" />
            <div className="text-left">
              <p className="font-medium text-primary">Excel (.xlsx)</p>
              <p className="text-xs text-muted">Microsoft Excel workbook</p>
            </div>
          </button>
          <div className="divider my-1" />
          <button
            onClick={() => {
              setOpen(false);
              if (!invoice?.extracted_data) return;
              const blob = new Blob([JSON.stringify(invoice.extracted_data, null, 2)], { type: 'application/json' });
              const url  = URL.createObjectURL(blob);
              const a    = document.createElement('a');
              a.href = url;
              a.download = `${invoice.filename.replace(/\.[^.]+$/, '')}_extracted.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-secondary hover:bg-[var(--color-bg-muted)] hover:text-primary transition-colors"
            role="menuitem"
          >
            <FileText className="h-4 w-4 text-amber-500 flex-shrink-0" />
            <div className="text-left">
              <p className="font-medium text-primary">JSON</p>
              <p className="text-xs text-muted">Raw extracted data</p>
            </div>
          </button>
        </div>
      )}
    </div>
  );
};

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

const REVIEW_STEPS: Array<{ status: InvoiceStatus; label: string }> = [
  { status: 'UPLOADED', label: 'Uploaded' },
  { status: 'OCR_COMPLETED', label: 'Text recognized' },
  { status: 'EXTRACTED', label: 'Fields extracted' },
];

const ReviewProgress: React.FC<{ status: InvoiceStatus }> = ({ status }) => {
  const currentIndex = status === 'FAILED'
    ? -1
    : REVIEW_STEPS.findIndex(step => step.status === status);

  return (
    <div className="card p-4" aria-label="Invoice processing progress">
      <div className="flex items-center justify-between gap-2">
        {REVIEW_STEPS.map((step, index) => {
          const complete = currentIndex >= index;
          return (
            <React.Fragment key={step.status}>
              <div className={`flex items-center gap-1.5 text-xs ${complete ? 'text-primary font-medium' : 'text-muted'}`}>
                <CheckCircle2 className={`h-4 w-4 ${complete ? 'text-emerald-500' : 'text-muted'}`} />
                <span className="hidden sm:inline">{step.label}</span>
                <span className="sm:hidden">{index + 1}</span>
              </div>
              {index < REVIEW_STEPS.length - 1 && (
                <div className={`h-px flex-1 ${currentIndex > index ? 'bg-emerald-500/60' : 'bg-[var(--color-border)]'}`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
      {status === 'FAILED' && (
        <p className="mt-3 text-xs text-red-600 dark:text-red-300">
          Processing stopped. Review the error below and retry when ready.
        </p>
      )}
    </div>
  );
};

/* ─── Invoice Viewer Page ───────────────────────────────── */
export const InvoiceViewerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: invoiceData, isLoading, isError, error } = useInvoice(id);
  const retryInvoice = useRetryInvoice();
  const extractInvoice = useExtractInvoice();
  const correctInvoice = useCorrectInvoice();
  const { toast } = useToast();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<ExtractedInvoiceData | null>(null);
  const data: ExtractedInvoiceData | undefined = invoiceData?.extracted_data;

  useEffect(() => {
    if (data && !editing) setDraft(data);
  }, [data, editing]);

  if (isLoading) return <PageSpinner label="Loading invoice details…" />;
  if (isError || !invoiceData) {
    return (
      <ErrorState
        title="Invoice not found"
        message={error instanceof Error ? error.message : 'This invoice could not be loaded.'}
        onRetry={() => navigate('/history')}
      />
    );
  }

  const currency = data?.currency ?? 'USD';
  const updateDraft = <K extends keyof ExtractedInvoiceData>(field: K, value: ExtractedInvoiceData[K]) => {
    setDraft(current => current ? { ...current, [field]: value } : current);
  };
  const handleSaveCorrections = async () => {
    if (!id || !draft) return;
    try {
      await correctInvoice.mutateAsync({ invoiceId: id, extractedData: draft });
      setEditing(false);
      toast.success('Corrections saved', 'The extracted invoice data was updated.');
    } catch (err) {
      toast.error('Could not save corrections', err instanceof Error ? err.message : 'Please try again.');
    }
  };
  const handleRetry = async () => {
    if (!id) return;
    try {
      await retryInvoice.mutateAsync(id);
      toast.success('Invoice processing restarted', 'The invoice was extracted successfully.');
    } catch (err) {
      toast.error(
        'Retry failed',
        err instanceof Error ? err.message : 'The invoice could not be processed again.',
      );
    }
  };
  const handleExtract = async () => {
    if (!id) return;
    try {
      await extractInvoice.mutateAsync(id);
      toast.success('Invoice extracted', 'The structured invoice data is ready for review.');
    } catch (err) {
      toast.error(
        'Extraction failed',
        err instanceof Error ? err.message : 'The invoice could not be extracted.',
      );
    }
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
            <h1 className="text-lg font-bold text-primary truncate">{invoiceData.filename}</h1>
            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
              <StatusBadge status={invoiceData.status} />
              <span className="text-xs text-muted">
                {new Date(invoiceData.created_at).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })}
              </span>
            </div>
          </div>
        </div>
        {/* Export Dropdown — disabled if not yet extracted */}
        <div className="flex-shrink-0">
          <div className="flex items-center gap-2">
            {data && (
              <button
                onClick={() => setEditing(value => !value)}
                className="btn btn-secondary btn-sm"
                disabled={correctInvoice.isPending}
              >
                {editing ? 'Cancel' : 'Edit fields'}
              </button>
            )}
            <ExportDropdown invoiceId={invoiceData.id} invoice={invoiceData} disabled={!data || editing} />
          </div>
        </div>
      </div>

      <ReviewProgress status={invoiceData.status} />

      {/* Confidence Meter */}
      {invoiceData.overall_confidence != null && (
        <div className="card p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-secondary">AI Extraction Confidence</span>
            <span className="text-xs text-muted">
              {invoiceData.extracted_data?.invoice_number
                ? `Invoice #${invoiceData.extracted_data.invoice_number}`
                : 'Unidentified'}
            </span>
          </div>
          <ConfidenceMeter value={invoiceData.overall_confidence} />
        </div>
      )}

      {invoiceData.status === 'FAILED' && (
        <div className="card border-red-500/30 bg-red-500/10 p-4" role="alert">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-red-700 dark:text-red-300">
                Invoice processing failed
              </p>
              <p className="text-xs text-secondary mt-1">
                {invoiceData.error_message || 'The document could not be processed.'}
              </p>
            </div>
            <button
              onClick={handleRetry}
              disabled={retryInvoice.isPending}
              className="btn btn-secondary btn-sm flex-shrink-0"
            >
              {retryInvoice.isPending ? <Spinner size="sm" /> : null}
              {retryInvoice.isPending ? 'Retrying…' : 'Retry processing'}
            </button>
          </div>
        </div>
      )}

      {['PENDING', 'UPLOADED', 'OCR_COMPLETED'].includes(invoiceData.status) && !data && (
        <div className="card border-blue-500/30 bg-blue-500/10 p-4" role="status">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-blue-700 dark:text-blue-300">
                {invoiceData.status === 'OCR_COMPLETED'
                  ? 'OCR is complete'
                  : 'Ready to process'}
              </p>
              <p className="text-xs text-secondary mt-1">
                {invoiceData.status === 'OCR_COMPLETED'
                  ? 'Review the recognized text below, then extract structured invoice fields.'
                  : 'Run OCR and AI extraction to review the invoice details.'}
              </p>
            </div>
            <button
              onClick={handleExtract}
              disabled={extractInvoice.isPending}
              className="btn btn-primary btn-sm flex-shrink-0"
            >
              {extractInvoice.isPending ? <Spinner size="sm" /> : null}
              {extractInvoice.isPending ? 'Processing…' : 'Extract invoice'}
            </button>
          </div>
        </div>
      )}

      {data?.validation_warnings && data.validation_warnings.length > 0 && (
        <div className="card border-amber-500/30 bg-amber-500/10 p-4" role="alert">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-amber-700 dark:text-amber-300">
                Review extracted amounts
              </p>
              <ul className="mt-1 space-y-1 text-xs text-secondary">
                {data.validation_warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Extracted Data Grid */}
      {data ? (
        <div className="space-y-5">
          <p className="text-xs text-secondary">
            {editing
              ? 'Correct any fields that do not match the original invoice, then save your changes.'
              : 'Review the extracted fields below against the original invoice before exporting.'}
          </p>
          {editing && draft ? (
            <form
              className="card p-5 space-y-5"
              onSubmit={(event) => {
                event.preventDefault();
                void handleSaveCorrections();
              }}
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {([
                  ['vendor_name', 'Vendor'],
                  ['vendor_address', 'Vendor address'],
                  ['customer_name', 'Customer'],
                  ['customer_address', 'Customer address'],
                  ['direction', 'Direction'],
                  ['invoice_number', 'Invoice number'],
                  ['invoice_date', 'Invoice date'],
                  ['due_date', 'Due date'],
                  ['currency', 'Currency'],
                  ['payment_terms', 'Payment terms'],
                ] as const).map(([field, label]) => (
                  <label key={field} className="space-y-1">
                    <span className="text-xs font-semibold text-secondary">{label}</span>
                    {field === 'direction' ? (
                      <select
                        className="input w-full"
                        value={draft[field]}
                        onChange={(event) => updateDraft(field, event.target.value as ExtractedInvoiceData['direction'])}
                      >
                        <option value="INCOMING">Incoming (payable)</option>
                        <option value="OUTGOING">Outgoing (receivable)</option>
                      </select>
                    ) : (
                      <input
                        className="input w-full"
                        value={draft[field] ?? ''}
                        onChange={(event) => updateDraft(field, event.target.value)}
                      />
                    )}
                  </label>
                ))}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {(['subtotal', 'tax', 'discount', 'total'] as const).map((field) => (
                  <label key={field} className="space-y-1">
                    <span className="text-xs font-semibold text-secondary capitalize">{field}</span>
                    <input
                      className="input w-full"
                      type="number"
                      min="0"
                      step="0.01"
                      value={draft[field]}
                      onChange={(event) => updateDraft(field, Number(event.target.value))}
                    />
                  </label>
                ))}
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setEditing(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm" disabled={correctInvoice.isPending}>
                  {correctInvoice.isPending ? <Spinner size="sm" /> : null}
                  {correctInvoice.isPending ? 'Saving…' : 'Save corrections'}
                </button>
              </div>
            </form>
          ) : (
          <>
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
              <Field label="Address" value={data.customer_address} />
              <Field label="Direction" value={data.direction === 'OUTGOING' ? 'Outgoing (receivable)' : 'Incoming (payable)'} />
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
          {(!data.invoice_items || data.invoice_items.length === 0) && (
            <div className="card border-amber-500/30 bg-amber-500/10 p-4 text-xs text-secondary">
              No line items were identified. Check the OCR preview before relying on the totals.
            </div>
          )}

          {/* Totals */}
          <div className="card p-5 max-w-xs ml-auto">
            <AmountField label="Subtotal" value={data.subtotal}  currency={currency} />
            {data.tax      > 0 && <AmountField label="Tax"      value={data.tax}      currency={currency} />}
            {data.discount > 0 && <AmountField label="Discount" value={-data.discount} currency={currency} />}
            <AmountField label="Total Due" value={data.total} currency={currency} highlight />
          </div>
          </>
          )}
        </div>
      ) : null}

      {invoiceData.raw_ocr_text && (
        <details className="card group">
          <summary className="cursor-pointer list-none p-5 text-sm font-semibold text-primary">
            <span className="flex items-center justify-between">
              OCR text preview
              <span className="text-xs font-normal text-muted group-open:hidden">Show</span>
              <span className="text-xs font-normal text-muted hidden group-open:inline">Hide</span>
            </span>
          </summary>
          <pre className="mx-5 mb-5 max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-[var(--color-bg-muted)] p-4 text-xs leading-relaxed text-secondary">
            {invoiceData.raw_ocr_text}
          </pre>
        </details>
      )}
    </div>
  );
};
