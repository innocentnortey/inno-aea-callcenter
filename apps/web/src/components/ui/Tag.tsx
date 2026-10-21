import { forwardRef, type HTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/cx";

export interface TagProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: "plain" | "strong";
  icon?: ReactNode;
}
/** Filled, 6 px corners, never an outlined pill. Strong = selected fill + 1 px ink edge. */
export const Tag = forwardRef<HTMLSpanElement, TagProps>(function Tag({ tone = "plain", icon, className, children, ...rest }, ref) {
  return (
    <span
      ref={ref}
      data-tone={tone}
      className={cn(
        "inline-flex items-center gap-1 rounded-tag px-2 py-0.5 text-small font-semibold",
        tone === "strong"
          ? "border border-[color:var(--tag-strong-edge)] bg-[var(--tag-strong-bg)] text-[color:var(--tag-text)]"
          : "border border-transparent bg-[var(--tag-bg)] text-[color:var(--tag-text)]",
        className,
      )}
      {...rest}
    >
      {icon}
      {children}
    </span>
  );
});
