import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import type { ToastItem, ToastType } from "../../context/toastContext";

interface ToastViewportProps {
  toasts: ToastItem[];
  onDismiss: (id: number) => void;
}

function ToastIcon({ type }: { type: ToastType }) {
  if (type === "error") {
    return <AlertCircle size={20} />;
  }

  if (type === "info") {
    return <Info size={20} />;
  }

  return <CheckCircle2 size={20} />;
}

export function ToastViewport({ toasts, onDismiss }: ToastViewportProps) {
  return (
    <div className="toast-viewport" aria-live="polite" aria-atomic="false">
      <AnimatePresence initial={false}>
        {toasts.map((toast) => (
          <motion.div
            className={`admin-toast admin-toast--${toast.type}`}
            key={toast.id}
            initial={{ opacity: 0, x: 28, scale: 0.96 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 22, scale: 0.96 }}
            transition={{
              duration: 0.22,
              ease: [0.22, 1, 0.36, 1],
            }}
          >
            <div className="admin-toast__icon">
              <ToastIcon type={toast.type} />
            </div>

            <div className="admin-toast__copy">
              <strong>{toast.title}</strong>

              {toast.message && <span>{toast.message}</span>}
            </div>

            <button
              type="button"
              aria-label="Dismiss notification"
              onClick={() => onDismiss(toast.id)}
            >
              <X size={17} />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
