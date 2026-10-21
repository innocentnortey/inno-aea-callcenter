import { forwardRef, type HTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/cx";

export const Card = forwardRef<HTMLElement, HTMLAttributes<HTMLElement>>(function Card({ className, ...rest }, ref) {
  return <section ref={ref} className={cn("overflow-hidden rounded-card border border-[color:var(--card-edge)] bg-[var(--card-bg)]", className)} {...rest} />;
});

export interface CardHeaderProps extends Omit<HTMLAttributes<HTMLDivElement>, "title"> {
  icon?: ReactNode;
  title: ReactNode;
  hint?: ReactNode;
  meta?: ReactNode;
  as?: "h2" | "h3" | "h4";
}
export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(function CardHeader({ icon, title, hint, meta, as: Tag = "h3", className, ...rest }, ref) {
  return (
    <div ref={ref} className={cn("flex items-center gap-2 border-b border-[color:var(--card-edge)] bg-[var(--card-head-bg)] px-3 py-2 text-accent", className)} {...rest}>
      {icon}
      <div className="min-w-0 flex-1">
        <Tag className="t-card-title text-text">{title}</Tag>
        {hint ? <p className="text-small text-text-muted">{hint}</p> : null}
      </div>
      {meta ? <div className="text-small text-text-muted">{meta}</div> : null}
    </div>
  );
});

export const CardBody = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(function CardBody({ className, ...rest }, ref) {
  return <div ref={ref} className={cn("p-3", className)} {...rest} />;
});

export interface CardRowProps extends Omit<HTMLAttributes<HTMLDivElement>, "children"> {
  label: ReactNode;
  hint?: ReactNode;
  mono?: boolean;
  children: ReactNode;
}
/** Dashed separator between rows; values right-aligned, 600, tabular. */
export const CardRow = forwardRef<HTMLDivElement, CardRowProps>(function CardRow({ label, hint, mono, children, className, ...rest }, ref) {
  return (
    <div ref={ref} className={cn("flex items-baseline justify-between gap-3 border-b border-dashed border-border-hair py-2 last:border-b-0", className)} {...rest}>
      <div>
        <span className="text-small text-text-muted">{label}</span>
        {hint ? <p className="text-caption text-text-muted">{hint}</p> : null}
      </div>
      <div className={cn("text-right text-ui font-semibold", mono && "t-ref")}>{children}</div>
    </div>
  );
});
