import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { invoiceApi } from '@/api/invoiceApi';
import { Invoice } from '@/types/invoice';

export const INVOICE_KEYS = {
  all:    ['invoices'] as const,
  list:   (params?: object) => ['invoices', 'list', params] as const,
  detail: (id: string) => ['invoices', 'detail', id] as const,
};

/** Fetch paginated invoice list */
export const useInvoices = (params?: { skip?: number; limit?: number; status?: string }) => {
  return useQuery({
    queryKey: INVOICE_KEYS.list(params),
    queryFn: () => invoiceApi.getInvoices(params),
    staleTime: 30_000,
  });
};

/** Fetch single invoice by ID */
export const useInvoice = (id: string | undefined) => {
  return useQuery({
    queryKey: INVOICE_KEYS.detail(id ?? ''),
    queryFn: () => invoiceApi.getInvoice(id!),
    enabled: !!id,
    staleTime: 10_000,
  });
};

/** Upload invoice file mutation */
export const useUploadInvoice = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => invoiceApi.uploadInvoice(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: INVOICE_KEYS.all });
    },
  });
};

/** Extract structured data from an uploaded invoice */
export const useExtractInvoice = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (invoiceId: string) => invoiceApi.extractInvoice(invoiceId),
    onSuccess: (data: Invoice) => {
      qc.setQueryData(INVOICE_KEYS.detail(data.id), data);
      qc.invalidateQueries({ queryKey: INVOICE_KEYS.all });
    },
  });
};

/** Combined upload + immediate extract mutation */
export const useProcessInvoice = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => invoiceApi.processInvoice(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: INVOICE_KEYS.all });
    },
  });
};
