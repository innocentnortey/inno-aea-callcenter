import { useEffect, useId, useRef, type ReactNode } from "react";
import { cn } from "@/lib/cx";

export interface DialogProps {
  open: boolean;
  onClose(): void;
  title: string;
  children: ReactNode;
  initialFocus?: "cancel" | "first";
  labelledBy?: string;
  className?: string;
}
/** Native <dialog> + showModal(): Escape closes, focus returns to the opener. */
export function Dialog({ open, onClose, title, children, initialFocus = "first", labelledBy, className }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const opener = useRef<Element | null>(null);
  const titleId = useId();

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) {
      opener.current = document.activeElement;
      d.showModal();
      const target = initialFocus === "cancel"
        ? d.querySelector<HTMLElement>("[data-dialog-cancel]")
        : d.querySelector<HTMLElement>("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
      target?.focus();
    } else if (!open && d.open) {
      d.close();
    }
  }, [open, initialFocus]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={labelledBy ?? titleId}
      className={cn("m-auto w-[min(92vw,440px)] rounded-card border-0 bg-[var(--dialog-bg)] p-4 text-text shadow-[var(--elev-popover)]", className)}
      onClose={() => {
        (opener.current as HTMLElement | null)?.focus?.();
        if (open) onClose();
      }}
      onCancel={() => undefined}
    >
      <h2 id={titleId} className="t-card-title mb-2">{title}</h2>
      {children}
    </dialog>
  );
}
