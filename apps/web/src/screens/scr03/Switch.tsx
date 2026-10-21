import { useId } from "react";

export interface SwitchProps {
  checked: boolean;
  onCheckedChange(next: boolean): void;
  label: string;
  hint?: string;
  disabled?: boolean;
  id?: string;
  describedBy?: string;
}

/** A native checkbox with role="switch": Space and click toggle it, the state is read from the input itself. */
export function Switch({ checked, onCheckedChange, label, hint, disabled, id, describedBy }: SwitchProps) {
  const auto = useId();
  const hintId = hint ? `${auto}-hint` : undefined;
  const labelId = `${auto}-label`;
  const described = [hintId, describedBy].filter(Boolean).join(" ") || undefined;
  return (
    <label className="flex min-h-11 items-center gap-3">
      <input
        id={id}
        type="checkbox"
        role="switch"
        className="peer sr-only"
        checked={checked}
        disabled={disabled}
        aria-labelledby={labelId}
        aria-describedby={described}
        onChange={(e) => onCheckedChange(e.target.checked)}
      />
      <span
        aria-hidden="true"
        className="relative h-6 w-11 shrink-0 rounded-full border border-[color:var(--field-edge)] bg-surface-well peer-checked:bg-[var(--color-accent)] peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-solid peer-focus-visible:outline-[color:var(--focus-ring)] peer-disabled:opacity-60 motion-safe:transition-colors"
      >
        <span className={`absolute top-0.5 left-0.5 size-4 rounded-full bg-[var(--card-bg)] border border-[color:var(--field-edge)] motion-safe:transition-transform ${checked ? "translate-x-5" : ""}`} />
      </span>
      <span className="flex flex-col">
        <span id={labelId} className="text-body font-semibold">{label}</span>
        {hint ? <span id={hintId} className="text-small text-text-muted">{hint}</span> : null}
      </span>
    </label>
  );
}
