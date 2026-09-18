import { type ReactNode, useCallback, useMemo, useRef, useState } from "react";
import { ToastViewport } from "../components/ui/ToastViewport";
import { ToastContext, type ToastInput, type ToastItem } from "./toastContext";

const TOAST_DURATION = 4200;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (input: ToastInput) => {
      const id = nextId.current++;

      const toast: ToastItem = {
        id,
        title: input.title,
        message: input.message,
        type: input.type ?? "success",
      };

      setToasts((current) => [...current, toast]);

      window.setTimeout(() => {
        dismissToast(id);
      }, TOAST_DURATION);
    },
    [dismissToast],
  );

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}

      <ToastViewport toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
}
