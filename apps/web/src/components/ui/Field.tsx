import { forwardRef, useId, type InputHTMLAttributes, type ReactNode, type TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/cx";
import { IconInfo } from "./icons";

export interface FieldIds { id: string; describedBy: string | undefined; invalid: boolean }
export interface FieldProps {
  label: string;
  hint?: string;
  error?: string;
  className?: string;
  children: (ids: FieldIds) => ReactNode;
}
/** A visible label, a hint under it, and an invalid state that is never red (ink edge + icon + message). */
export function Field({ label, hint, error, className, children }: FieldProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errId = error ? `${id}-err` : undefined;
  const describedBy = [hintId, errId].filter(Boolean).join(" ") || undefined;
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <label htmlFor={id} className="text-small font-semibold">{label}</label>
      {hint ? <p id={hintId} className="text-small text-text-muted">{hint}</p> : null}
      {children({ id, describedBy, invalid: Boolean(error) })}
      {error ? (
        <p id={errId} className="flex items-center gap-1 text-small">
          <IconInfo size={14} strokeWidth={1.8} aria-hidden="true" />
          {error}
        </p>
      ) : null}
    </div>
  );
}

const control =
  "w-full rounded-control bg-[var(--field-bg)] px-3 text-body text-text border border-[color:var(--field-edge)] focus:border-[color:var(--field-focus-edge)] disabled:text-text-muted disabled:border-transparent aria-[invalid=true]:border-2 aria-[invalid=true]:border-[color:var(--field-invalid-edge)]";

export interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> { invalid?: boolean; density?: "chat" | "console" }
export const TextInput = forwardRef<HTMLInputElement, TextInputProps>(function TextInput({ invalid, density = "chat", className, ...rest }, ref) {
  return (
    <input
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(control, density === "chat" ? "min-h-[var(--target-min)]" : "min-h-[var(--target-min)] min-[700px]:min-h-[var(--control-h-console)] pointer-coarse:min-h-[var(--target-min)] text-ui", className)}
      {...rest}
    />
  );
});

export interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> { invalid?: boolean; density?: "chat" | "console" }
export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(function TextArea({ invalid, density = "chat", className, ...rest }, ref) {
  return (
    <textarea
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(control, "py-2", density === "chat" ? "min-h-[var(--composer-min-h)]" : "min-h-[var(--target-min)] min-[700px]:min-h-[var(--control-h-console)] pointer-coarse:min-h-[var(--target-min)] text-ui", className)}
      {...rest}
    />
  );
});

export interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> { label: string }
export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(function Checkbox({ label, className, id, ...rest }, ref) {
  const auto = useId();
  const cid = id ?? auto;
  return (
    <span className={cn("inline-flex min-h-[var(--target-min)] items-center gap-2", className)}>
      <input ref={ref} id={cid} type="checkbox" className="size-4 accent-[var(--color-accent)]" {...rest} />
      <label htmlFor={cid} className="text-body">{label}</label>
    </span>
  );
});
