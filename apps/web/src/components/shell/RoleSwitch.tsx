import * as RadioGroup from "@radix-ui/react-radio-group";
import { cn } from "@/lib/cx";
import { ROLES, ROLE_LABEL, type Role } from "@/lib/roles";
import { useSession } from "@/state/session";
import { IconCheck } from "@/components/ui/icons";

export interface RoleSwitchProps { variant?: "segmented" | "row"; density?: "chat" | "console"; className?: string }

/** Four roles, always visible, never in a menu. The current one is marked, ticked and named "current". */
export function RoleSwitch({ variant = "segmented", density = "chat", className }: RoleSwitchProps) {
  const { role, switching, switchError, switchRole } = useSession();
  const disabled = switching !== null;
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <RadioGroup.Root
        aria-label="Acting as"
        value={role ?? ""}
        onValueChange={(v) => { if (v !== role) void switchRole(v as Role); }}
        disabled={disabled}
        orientation="horizontal"
        className={cn("flex w-full gap-2", variant === "row" && "min-h-[var(--target-min)]")}
      >
        {ROLES.map((r) => {
          const current = r === role;
          const label = ROLE_LABEL[r];
          return (
            <RadioGroup.Item
              key={r}
              value={r}
              aria-label={label.full + (current ? ", current" : "")}
              className={cn(
                "motion-control flex flex-1 items-center justify-center gap-1 rounded-control border px-2 text-ui font-semibold disabled:cursor-not-allowed",
                density === "chat" ? "min-h-[var(--target-min)]" : "min-h-[var(--target-min)] min-[700px]:min-h-[var(--control-h-console)] pointer-coarse:min-h-[var(--target-min)]",
                current
                  ? "border-[color:var(--tag-strong-edge)] bg-surface-selected text-text"
                  : "border-border-hair bg-surface text-text [--hover-base:var(--color-surface)] hover-mix",
              )}
            >
              {switching === r ? (
                <span>Switching{"…"}</span>
              ) : (
                <>
                  {current ? <IconCheck size={14} strokeWidth={1.8} aria-hidden="true" /> : null}
                  <span className="hidden min-[700px]:inline" aria-hidden="true">{label.short}</span>
                  <span className="min-[700px]:hidden" aria-hidden="true">{label.phone}</span>
                </>
              )}
            </RadioGroup.Item>
          );
        })}
      </RadioGroup.Root>
      {switchError ? <p role="status" className="text-small">{switchError}</p> : null}
    </div>
  );
}
