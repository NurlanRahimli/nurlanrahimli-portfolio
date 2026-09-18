import { createContext, useContext } from "react";

export type ToastType = "success" | "error" | "info";

export interface ToastInput {
  title: string;
  message?: string;
  type?: ToastType;
}

export interface ToastItem extends ToastInput {
  id: number;
  type: ToastType;
}

export interface ToastContextValue {
  showToast: (toast: ToastInput) => void;
}

export const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }

  return context;
}
