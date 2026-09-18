import { ExtractedInvoiceData, HealthStatus, Invoice } from '../types/invoice';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    let code = 'HTTP_ERROR';
    try {
      const err = await res.json();
      message = err.message ?? err.detail ?? message;
      code = err.error_code ?? code;
    } catch {
      // ignore JSON parse error
    }
    throw new ApiError(message, res.status, code);
  }
  return res.json() as Promise<T>;
}

export const invoiceApi = {
  getHealth: async (): Promise<HealthStatus> => {
    const res = await fetch(`${API_BASE_URL}/health`);
    return handleResponse<HealthStatus>(res);
  },

  uploadInvoice: async (file: File): Promise<Invoice> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/invoices/upload`, { method: 'POST', body: formData });
    return handleResponse<Invoice>(res);
  },

  extractInvoice: async (invoiceId: string): Promise<Invoice> => {
    const res = await fetch(`${API_BASE_URL}/invoices/${invoiceId}/extract`, { method: 'POST' });
    return handleResponse<Invoice>(res);
  },

  retryInvoice: async (invoiceId: string): Promise<Invoice> => {
    const res = await fetch(`${API_BASE_URL}/invoices/${invoiceId}/retry`, { method: 'POST' });
    return handleResponse<Invoice>(res);
  },

  processInvoice: async (file: File): Promise<Invoice> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/invoices/process`, { method: 'POST', body: formData });
    return handleResponse<Invoice>(res);
  },

  getInvoice: async (invoiceId: string): Promise<Invoice> => {
    const res = await fetch(`${API_BASE_URL}/invoices/${invoiceId}`);
    return handleResponse<Invoice>(res);
  },

  deleteInvoice: async (invoiceId: string): Promise<void> => {
    const res = await fetch(`${API_BASE_URL}/invoices/${invoiceId}`, { method: 'DELETE' });
    if (!res.ok) {
      await handleResponse<never>(res);
    }
  },

  correctInvoice: async (invoiceId: string, extractedData: ExtractedInvoiceData): Promise<Invoice> => {
    const res = await fetch(`${API_BASE_URL}/invoices/${invoiceId}/extracted-data`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(extractedData),
    });
    return handleResponse<Invoice>(res);
  },

  getInvoices: async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
    search?: string;
  }): Promise<{ total: number; items: Invoice[] }> => {
    const qs = new URLSearchParams();
    if (params?.skip  !== undefined) qs.set('skip',  String(params.skip));
    if (params?.limit !== undefined) qs.set('limit', String(params.limit));
    if (params?.status)              qs.set('status', params.status);
    if (params?.search?.trim())     qs.set('search', params.search.trim());
    const res = await fetch(`${API_BASE_URL}/invoices?${qs.toString()}`);
    return handleResponse<{ total: number; items: Invoice[] }>(res);
  },

  /**
   * Triggers a browser file download for the exported invoice.
   * Handled client-side (no navigation) via a Blob + Object URL.
   */
  exportInvoice: async (invoiceId: string, format: 'csv' | 'xlsx'): Promise<void> => {
    const res = await fetch(`${API_BASE_URL}/invoices/${invoiceId}/export?format=${format}`);
    if (!res.ok) {
      let message = `Export failed: HTTP ${res.status}`;
      try {
        const err = await res.json();
        message = err.message ?? err.detail ?? message;
      } catch { /* ignore */ }
      throw new Error(message);
    }
    const blob = await res.blob();
    const contentDisposition = res.headers.get('Content-Disposition') ?? '';
    const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
    const filename = filenameMatch?.[1] ?? `invoice_export.${format}`;
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  },
};
