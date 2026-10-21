import { type HTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/cx";

export function VisuallyHidden({ children }: { children: ReactNode }) {
  return <span className="sr-only">{children}</span>;
}
export function Kbd({ children, className, ...rest }: HTMLAttributes<HTMLElement>) {
  return <kbd className={cn("rounded-tag bg-[var(--tag-bg)] px-1.5 py-0.5 text-caption text-text-muted", className)} {...rest}>{children}</kbd>;
}
