import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, ArrowRight, Lightbulb } from 'lucide-react';
import { FileDropZone } from '@/components/upload/FileDropZone';
import { ProcessingSteps } from '@/components/common/Spinner';
import { useUploadInvoice, useExtractInvoice } from '@/hooks/useInvoices';
import { useToast } from '@/context/ToastContext';

type Stage = 'idle' | 'uploading' | 'extracting' | 'done' | 'error';

const STEPS = [
  { label: 'Validating and uploading document' },
  { label: 'Running OCR text recognition' },
  { label: 'AI structured data extraction' },
  { label: 'Saving results to database' },
];

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [stage, setStage] = useState<Stage>('idle');
  const [activeStep, setActiveStep] = useState<number>(-1);
  const [resultId, setResultId] = useState<string | null>(null);

  const upload  = useUploadInvoice();
  const extract = useExtractInvoice();

  const handleFiles = async (files: File[]) => {
    const file = files[0];
    if (!file) return;

    try {
      // Step 0: Upload
      setStage('uploading');
      setActiveStep(0);
      const uploadedInvoice = await upload.mutateAsync(file);
      setActiveStep(1);

      // Step 1–2: Extract (OCR + LLM happen server side)
      setStage('extracting');
      const processed = await extract.mutateAsync(uploadedInvoice.id);
      setActiveStep(3);

      setResultId(processed.id);
      setStage('done');
      toast.success('Invoice processed successfully', `${file.name} has been extracted.`);
    } catch (err: unknown) {
      setStage('error');
      setActiveStep(-1);
      const msg = err instanceof Error ? err.message : 'Processing failed.';
      toast.error('Processing failed', msg);
    }
  };

  const processingSteps = STEPS.map((s, i) => ({
    label: s.label,
    done:   stage === 'done' || (stage !== 'idle' && i < activeStep),
    active: activeStep === i && stage !== 'done' && stage !== 'error',
  }));

  const isProcessing = stage === 'uploading' || stage === 'extracting';

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-primary">Upload Invoice</h1>
        <p className="text-sm text-secondary mt-0.5">
          Upload a PDF, PNG, JPG, or JPEG file. Our AI pipeline will extract all structured data automatically.
        </p>
      </div>

      {/* Upload Card */}
      <div className="card p-6 space-y-6">
        {stage === 'idle' || stage === 'error' ? (
          <FileDropZone
            onFilesAccepted={handleFiles}
            disabled={isProcessing}
          />
        ) : stage === 'done' ? (
          /* Success State */
          <div className="flex flex-col items-center text-center py-10 gap-4 animate-slide-up">
            <div className="w-14 h-14 rounded-full bg-[var(--color-success-bg)] flex items-center justify-center">
              <svg className="h-7 w-7 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h3 className="text-base font-semibold text-primary">Extraction Complete</h3>
              <p className="text-sm text-secondary mt-1">
                All invoice data has been extracted and saved.
              </p>
            </div>
            <div className="flex flex-wrap gap-3 justify-center mt-2">
              <button
                onClick={() => resultId && navigate(`/invoices/${resultId}`)}
                className="btn btn-primary"
              >
                <FileText className="h-4 w-4" />
                View Extracted Data
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => { setStage('idle'); setActiveStep(-1); setResultId(null); }}
                className="btn btn-secondary"
              >
                Upload Another
              </button>
            </div>
          </div>
        ) : null}

        {/* Processing Panel */}
        {isProcessing && (
          <div className="animate-slide-up space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-1 h-8 rounded-full bg-brand-600 animate-pulse-soft" aria-hidden="true" />
              <div>
                <p className="text-sm font-semibold text-primary">Processing your document…</p>
                <p className="text-xs text-secondary">Please wait. This usually takes 10–30 seconds.</p>
              </div>
            </div>
            <ProcessingSteps steps={processingSteps} />
          </div>
        )}
      </div>

      {/* Tip Card */}
      {stage === 'idle' && (
        <div className="flex items-start gap-3 px-4 py-3.5 rounded-xl bg-[var(--color-bg-muted)] border border-[var(--color-border)]">
          <Lightbulb className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-primary">Best results</p>
            <p className="text-xs text-secondary mt-0.5 leading-relaxed">
              Upload clear, unrotated scans or digital PDFs. Ensure text is legible and images are at least 150 DPI for accurate OCR output.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
