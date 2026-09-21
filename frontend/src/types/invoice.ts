export type InvoiceStatus = 'PENDING' | 'UPLOADED' | 'OCR_COMPLETED' | 'EXTRACTED' | 'FAILED';

export interface InvoiceItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface ExtractedInvoiceData {
  invoice_number?: string;
  vendor_name?: string;
  vendor_address?: string;
  customer_name?: string;
  customer_address?: string;
  invoice_date?: string;
  due_date?: string;
  currency: string;
  subtotal: number;
  tax: number;
  discount: number;
  total: number;
  payment_terms?: string;
  invoice_items: InvoiceItem[];
  confidence_score: number;
  validation_warnings?: string[];
}

export interface OCRMetadata {
  raw_text?: string;
  pages?: number;
  detected_language?: string;
  confidence?: number;
}

export interface Invoice {
  id: string;
  filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  status: InvoiceStatus;
  error_message?: string;
  raw_ocr_text?: string;
  ocr_metadata?: OCRMetadata;
  extracted_data?: ExtractedInvoiceData;
  overall_confidence?: number;
  created_at: string;
  updated_at: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
  database: string;
  migration: string;
  ocr_provider: string;
  ocr_configured: boolean;
  poppler_configured: boolean;
  llm_provider: string;
  llm_model: string;
  llm_configured: boolean;
  storage_provider: string;
}
