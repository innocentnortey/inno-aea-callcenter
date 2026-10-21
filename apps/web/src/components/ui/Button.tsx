import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/cx";

const button = cva(
  "motion-control inline-flex items-center justify-center gap-2 rounded-control px-4 font-semibold disabled:cursor-not-allowed disabled:bg-surface-well disabled:text-text-muted disabled:border-transparent",
  {
    variants: {
      variant: {
        primary: "bg-[var(--btn-primary-bg)] text-[color:var(--btn-primary-text)] border border-transparent [--hover-base:var(--btn-primary-bg)] hover-mix press-mix",
        secondary: "bg-[var(--btn-secondary-bg)] text-text border border-border-hair [--hover-base:var(--btn-secondary-bg)] hover-mix press-mix",
        send: "bg-[var(--btn-send-bg)] text-[color:var(--btn-send-text)] border border-transparent [--hover-base:var(--btn-send-bg)] hover-mix press-mix",
        text: "bg-transparent text-[color:var(--btn-ghost-text)] border border-transparent px-1 link-text",
      },
      density: {
        chat: "min-h-[var(--target-min)] text-body",
        console: "min-h-[var(--target-min)] min-[700px]:min-h-[var(--control-h-console)] pointer-coarse:min-h-[var(--target-min)] text-ui",
      },
    },
    defaultVariants: { variant: "secondary", density: "chat" },
  },
);

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "send" | "text";
  density?: "chat" | "console";
  loading?: boolean;
  icon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant, density, loading, icon, className, children, disabled, type = "button", ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cn(button({ variant, density }), className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {icon}
      {children}
    </button>
  );
});
