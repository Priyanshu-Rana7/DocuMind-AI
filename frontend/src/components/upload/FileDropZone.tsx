import React, { useRef, useState, useCallback } from 'react';
import clsx from 'clsx';
import { UploadCloud, FileText, Image, X, AlertCircle, CheckCircle2 } from 'lucide-react';

interface FileDropZoneProps {
  onFilesAccepted: (files: File[]) => void;
  accept?: string[];
  maxSizeMb?: number;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
}

const ALLOWED_TYPES = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
const EXT_LABELS = 'PDF, PNG, JPG, JPEG';

interface FileMeta {
  file: File;
  valid: boolean;
  error?: string;
}

const formatBytes = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
};

const fileIcon = (type: string) => {
  if (type === 'application/pdf')  return <FileText className="h-5 w-5 text-red-500" />;
  return <Image className="h-5 w-5 text-blue-500" />;
};

export const FileDropZone: React.FC<FileDropZoneProps> = ({
  onFilesAccepted,
  accept = ALLOWED_TYPES,
  maxSizeMb = 15,
  multiple = false,
  disabled = false,
  className,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setDragging] = useState(false);
  const [queue, setQueue] = useState<FileMeta[]>([]);

  const validate = useCallback((files: File[]): FileMeta[] => {
    return files.map(f => {
      if (!accept.includes(f.type))
        return { file: f, valid: false, error: `Unsupported type. Allowed: ${EXT_LABELS}` };
      if (f.size > maxSizeMb * 1024 * 1024)
        return { file: f, valid: false, error: `Exceeds ${maxSizeMb} MB limit` };
      if (f.size === 0)
        return { file: f, valid: false, error: 'File is empty' };
      return { file: f, valid: true };
    });
  }, [accept, maxSizeMb]);

  const handleFiles = useCallback((rawFiles: File[]) => {
    const files = multiple ? rawFiles : rawFiles.slice(0, 1);
    const validated = validate(files);
    setQueue(validated);
    const valid = validated.filter(f => f.valid).map(f => f.file);
    if (valid.length > 0) onFilesAccepted(valid);
  }, [multiple, validate, onFilesAccepted]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (!disabled) handleFiles(Array.from(e.dataTransfer.files));
  };

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) handleFiles(Array.from(e.target.files));
  };

  const removeFromQueue = (idx: number) => {
    setQueue(prev => prev.filter((_, i) => i !== idx));
  };

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Drop Zone */}
      <div
        onClick={() => !disabled && inputRef.current?.click()}
        onDragEnter={e => { e.preventDefault(); if (!disabled) setDragging(true); }}
        onDragOver={e => { e.preventDefault(); if (!disabled) setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload invoice file. Click or drag and drop."
        onKeyDown={e => e.key === 'Enter' && !disabled && inputRef.current?.click()}
        className={clsx(
          'relative flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-10 text-center cursor-pointer select-none',
          'transition-all duration-200',
          isDragging && !disabled
            ? 'border-[var(--color-brand-500)] bg-[var(--color-brand-50)] dark:bg-[color-mix(in_srgb,var(--color-brand-500)_8%,transparent)] scale-[1.005]'
            : 'border-[var(--color-border)] bg-[var(--color-bg-subtle)] hover:border-[var(--color-border-strong)] hover:bg-[var(--color-bg-muted)]',
          disabled && 'opacity-50 cursor-not-allowed',
        )}
      >
        <div className={clsx(
          'flex items-center justify-center w-14 h-14 rounded-2xl border transition-colors duration-200',
          isDragging
            ? 'border-[var(--color-brand-400)] bg-[var(--color-brand-100)] dark:bg-[color-mix(in_srgb,var(--color-brand-500)_20%,transparent)] text-[var(--color-brand-600)]'
            : 'border-[var(--color-border)] bg-[var(--color-bg-base)] text-muted',
        )}>
          <UploadCloud className="h-7 w-7" />
        </div>
        <div>
          <p className="text-sm font-medium text-primary">
            {isDragging ? 'Drop to upload' : 'Drag & drop or click to upload'}
          </p>
          <p className="text-xs text-muted mt-1">{EXT_LABELS} · Max {maxSizeMb} MB</p>
        </div>
        <input
          ref={inputRef}
          type="file"
          className="sr-only"
          accept={accept.join(',')}
          multiple={multiple}
          disabled={disabled}
          onChange={onInputChange}
          aria-hidden="true"
        />
      </div>

      {/* File Queue */}
      {queue.length > 0 && (
        <ul className="space-y-2" role="list" aria-label="Selected files">
          {queue.map((meta, i) => (
            <li
              key={`${meta.file.name}-${i}`}
              className={clsx(
                'flex items-center gap-3 px-4 py-3 rounded-lg border text-sm',
                meta.valid
                  ? 'border-[var(--color-border)] bg-[var(--color-bg-subtle)]'
                  : 'border-red-200 bg-[var(--color-error-bg)] dark:border-red-900',
              )}
            >
              {fileIcon(meta.file.type)}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-primary truncate-text">{meta.file.name}</p>
                <p className="text-xs text-muted">
                  {formatBytes(meta.file.size)}
                  {meta.error && (
                    <span className="text-red-600 dark:text-red-400 ml-2 flex items-center gap-1 inline-flex">
                      <AlertCircle className="h-3 w-3" /> {meta.error}
                    </span>
                  )}
                </p>
              </div>
              {meta.valid && <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />}
              <button
                onClick={e => { e.stopPropagation(); removeFromQueue(i); }}
                className="btn btn-ghost btn-sm p-1 ml-1 text-muted flex-shrink-0"
                aria-label={`Remove ${meta.file.name}`}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
