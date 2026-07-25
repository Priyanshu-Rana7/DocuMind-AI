import { HealthStatus, Invoice } from '../types/invoice';

const API_BASE_URL = '/api/v1';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      message = err.message ?? err.detail ?? message;
    } catch {
      // ignore JSON parse error
    }
    throw new Error(message);
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

  getInvoices: async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
  }): Promise<{ total: number; items: Invoice[] }> => {
    const qs = new URLSearchParams();
    if (params?.skip  !== undefined) qs.set('skip',  String(params.skip));
    if (params?.limit !== undefined) qs.set('limit', String(params.limit));
    if (params?.status)              qs.set('status', params.status);
    const res = await fetch(`${API_BASE_URL}/invoices?${qs.toString()}`);
    return handleResponse<{ total: number; items: Invoice[] }>(res);
  },
};
