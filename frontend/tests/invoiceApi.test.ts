import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, invoiceApi } from '@/api/invoiceApi';

describe('invoiceApi', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('serializes pagination, status, and search parameters', async () => {
    const response = {
      ok: true,
      json: vi.fn().mockResolvedValue({ total: 0, items: [] }),
    } as unknown as Response;
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response);

    await invoiceApi.getInvoices({
      skip: 20,
      limit: 20,
      status: 'EXTRACTED',
      search: ' Samsung India ',
    });

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/invoices?skip=20&limit=20&status=EXTRACTED&search=Samsung+India',
    );
  });

  it('preserves backend error codes for recovery decisions', async () => {
    const response = {
      ok: false,
      status: 503,
      json: vi.fn().mockResolvedValue({
        error_code: 'LLM_CONFIGURATION_ERROR',
        message: 'Provider is not configured.',
      }),
    } as unknown as Response;
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(response);

    const request = invoiceApi.extractInvoice('invoice-1');

    await expect(request).rejects.toMatchObject({
      name: 'ApiError',
      status: 503,
      code: 'LLM_CONFIGURATION_ERROR',
      message: 'Provider is not configured.',
    } satisfies Partial<ApiError>);
  });

  it('uploads invoices as multipart form data', async () => {
    const response = {
      ok: true,
      json: vi.fn().mockResolvedValue({ id: 'invoice-1' }),
    } as unknown as Response;
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response);
    const file = new File(['invoice'], 'invoice.pdf', { type: 'application/pdf' });

    await invoiceApi.uploadInvoice(file);

    const [, options] = fetchMock.mock.calls[0];
    expect(options?.method).toBe('POST');
    expect(options?.body).toBeInstanceOf(FormData);
    expect((options?.body as FormData).get('file')).toBe(file);
  });
});
