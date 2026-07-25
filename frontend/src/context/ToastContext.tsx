import React, { createContext, useContext, useCallback, useState } from 'react';
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  exiting?: boolean;
}

interface ToastContextValue {
  toast: {
    success: (title: string, message?: string) => void;
    error:   (title: string, message?: string) => void;
    info:    (title: string, message?: string) => void;
    warning: (title: string, message?: string) => void;
  };
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

const icons: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle  className="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" />,
  error:   <AlertCircle  className="h-4 w-4 text-red-500     flex-shrink-0 mt-0.5" />,
  info:    <Info         className="h-4 w-4 text-blue-500    flex-shrink-0 mt-0.5" />,
  warning: <AlertTriangle className="h-4 w-4 text-amber-500  flex-shrink-0 mt-0.5" />,
};

const titleColors: Record<ToastType, string> = {
  success: 'text-emerald-700 dark:text-emerald-300',
  error:   'text-red-700     dark:text-red-300',
  info:    'text-blue-700    dark:text-blue-300',
  warning: 'text-amber-700   dark:text-amber-300',
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.map(t => t.id === id ? { ...t, exiting: true } : t));
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 220);
  }, []);

  const addToast = useCallback((type: ToastType, title: string, message?: string) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    setToasts(prev => [...prev, { id, type, title, message }]);
    setTimeout(() => dismiss(id), 4500);
  }, [dismiss]);

  const toast = {
    success: (title: string, message?: string) => addToast('success', title, message),
    error:   (title: string, message?: string) => addToast('error',   title, message),
    info:    (title: string, message?: string) => addToast('info',    title, message),
    warning: (title: string, message?: string) => addToast('warning', title, message),
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="toast-container" role="region" aria-label="Notifications" aria-live="polite">
        {toasts.map(t => (
          <div key={t.id} className={`toast ${t.exiting ? 'toast-exit' : ''}`} role="alert">
            {icons[t.type]}
            <div className="flex-1 min-w-0">
              <p className={`font-medium text-sm leading-tight ${titleColors[t.type]}`}>{t.title}</p>
              {t.message && <p className="text-xs text-secondary mt-0.5 leading-relaxed">{t.message}</p>}
            </div>
            <button
              onClick={() => dismiss(t.id)}
              className="btn-ghost btn btn-sm p-1 ml-1 flex-shrink-0"
              aria-label="Dismiss notification"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextValue => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
};
