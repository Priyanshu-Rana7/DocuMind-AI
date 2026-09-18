import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FileText, ChevronLeft, ChevronRight, Upload, Trash2 } from 'lucide-react';
import { useDeleteInvoice, useInvoices } from '@/hooks/useInvoices';
import { useToast } from '@/context/ToastContext';
import { StatusBadge } from '@/components/common/Badge';
import { SkeletonTableRow } from '@/components/common/Skeleton';
import { EmptyState } from '@/components/common/EmptyState';
import { InvoiceStatus } from '@/types/invoice';

const STATUS_FILTERS: Array<{ label: string; value: InvoiceStatus | '' }> = [
  { label: 'All',       value: '' },
  { label: 'Extracted', value: 'EXTRACTED' },
  { label: 'Uploaded',  value: 'UPLOADED' },
  { label: 'Failed',    value: 'FAILED' },
];

const PAGE_SIZE = 20;

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [search,    setSearch]    = useState('');
  const [statusFilter, setStatus] = useState<InvoiceStatus | ''>('');
  const [page,      setPage]      = useState(0);
  const deleteInvoice = useDeleteInvoice();
  const { toast } = useToast();

  const { data, isLoading, isError, refetch } = useInvoices({
    skip:   page * PAGE_SIZE,
    limit:  PAGE_SIZE,
    status: statusFilter || undefined,
    search: search.trim() || undefined,
  });

  const invoices   = data?.items ?? [];
  const totalCount = data?.total ?? 0;
  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  const handleDelete = async (invoiceId: string, filename: string) => {
    if (!window.confirm(`Permanently delete "${filename}" and its extracted data?`)) return;
    try {
      await deleteInvoice.mutateAsync(invoiceId);
      toast.success('Invoice deleted', 'The source file and extracted data were removed.');
    } catch (err) {
      toast.error('Delete failed', err instanceof Error ? err.message : 'The invoice could not be deleted.');
    }
  };

  const fmtDate = (iso: string) =>
    new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

  const fmtAmount = (inv: typeof invoices[0]) => {
    const t = inv.extracted_data?.total;
    if (t == null) return '—';
    return `${inv.extracted_data?.currency ?? 'USD'} ${t.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-primary">Invoice History</h1>
          <p className="text-sm text-secondary mt-0.5">
            {totalCount > 0 ? `${totalCount} document${totalCount !== 1 ? 's' : ''} processed` : 'All processed invoices'}
          </p>
        </div>
        <button onClick={() => navigate('/upload')} className="btn btn-primary btn-sm">
          <Upload className="h-3.5 w-3.5" /> Upload New
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted pointer-events-none" />
          <input
            type="search"
            placeholder="Search by filename, vendor, invoice number…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(0); }}
            className="input pl-8"
            aria-label="Search invoices"
          />
        </div>

        {/* Status Filter Pills */}
        <div className="flex gap-1.5 flex-wrap" role="group" aria-label="Filter by status">
          {STATUS_FILTERS.map(f => (
            <button
              key={f.value}
              onClick={() => { setStatus(f.value as InvoiceStatus | ''); setPage(0); }}
              className={`btn btn-sm ${statusFilter === f.value ? 'btn-primary' : 'btn-secondary'}`}
              aria-pressed={statusFilter === f.value}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isError ? (
          <EmptyState
            icon={<FileText className="h-6 w-6" />}
            title="Failed to load invoices"
            description="There was a problem fetching your invoice history."
            action={
              <button onClick={() => refetch()} className="btn btn-secondary btn-sm">Retry</button>
            }
          />
        ) : (
          <>
            <div className="table-wrapper">
              <table className="data-table" role="table" aria-label="Invoice history">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Vendor</th>
                    <th>Invoice #</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th className="text-right">Total</th>
                    <th className="w-12" aria-label="Actions"></th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading
                    ? Array.from({ length: 8 }).map((_, i) => <SkeletonTableRow key={i} cols={6} />)
                    : invoices.length === 0
                      ? (
                        <tr>
                          <td colSpan={7} className="border-none">
                            <EmptyState
                              icon={<FileText className="h-6 w-6" />}
                              title="No invoices found"
                              description={search ? 'Try a different search term.' : 'Upload your first invoice to get started.'}
                              action={!search ? (
                                <button onClick={() => navigate('/upload')} className="btn btn-primary btn-sm">
                                  Upload Invoice
                                </button>
                              ) : undefined}
                            />
                          </td>
                        </tr>
                      )
                      : invoices.map(inv => (
                        <tr
                          key={inv.id}
                          onClick={() => navigate(`/invoices/${inv.id}`)}
                          className="cursor-pointer"
                          tabIndex={0}
                          role="row"
                          onKeyDown={e => e.key === 'Enter' && navigate(`/invoices/${inv.id}`)}
                          aria-label={`Open ${inv.filename}`}
                        >
                          <td>
                            <div className="flex items-center gap-2.5">
                              <div className="w-7 h-7 rounded-md bg-[var(--color-bg-muted)] flex items-center justify-center flex-shrink-0">
                                <FileText className="h-3.5 w-3.5 text-secondary" />
                              </div>
                              <span className="text-sm font-medium text-primary truncate-text max-w-[160px]">
                                {inv.filename}
                              </span>
                            </div>
                          </td>
                          <td className="text-sm">
                            {inv.extracted_data?.vendor_name ?? <span className="text-muted">—</span>}
                          </td>
                          <td className="text-sm font-mono text-secondary">
                            {inv.extracted_data?.invoice_number ?? <span className="text-muted">—</span>}
                          </td>
                          <td className="text-sm text-secondary whitespace-nowrap">
                            {fmtDate(inv.created_at)}
                          </td>
                          <td><StatusBadge status={inv.status} /></td>
                          <td className="text-sm font-medium text-primary text-right whitespace-nowrap">
                            {fmtAmount(inv)}
                          </td>
                          <td className="text-right">
                            <button
                              onClick={(event) => {
                                event.stopPropagation();
                                void handleDelete(inv.id, inv.filename);
                              }}
                              className="btn btn-ghost btn-sm p-1.5 text-red-600 hover:text-red-700"
                              aria-label={`Delete ${inv.filename}`}
                              disabled={deleteInvoice.isPending}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))
                  }
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-5 py-3 border-t border-[var(--color-border)] text-xs text-secondary">
                <span>
                  Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, totalCount)} of {totalCount}
                </span>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className="btn btn-ghost btn-sm p-1.5"
                    aria-label="Previous page"
                  >
                    <ChevronLeft className="h-3.5 w-3.5" />
                  </button>
                  <span className="px-2 font-medium">{page + 1} / {totalPages}</span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                    disabled={page >= totalPages - 1}
                    className="btn btn-ghost btn-sm p-1.5"
                    aria-label="Next page"
                  >
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
