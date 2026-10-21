import { Tag, VisuallyHidden } from "@/components/ui";
import type { Role } from "@/lib/roles";
import { CURRENT, SWITCHING } from "./copy";

export interface RoleChoice { role: Role; title: string; line: string | null }
export interface RoleChoicesProps {
  roles: RoleChoice[];
  current: Role | null;
  switching: Role | null;
  onPick(role: Role): void;
}

const CARD = "flex w-full min-h-11 flex-col items-start gap-1 rounded-card border border-[color:var(--card-edge)] bg-[var(--card-bg)] p-3 text-left";

export function RoleChoices({ roles, current, switching, onPick }: RoleChoicesProps) {
  return (
    <ul className="mt-4 flex flex-col gap-3">
      {roles.map((r) => (
        <li key={r.role}>
          {r.role === current ? (
            <div aria-current="true" className={CARD}>
              <span className="flex items-center gap-2 font-semibold">
                {r.title}
                <Tag tone="strong" aria-hidden="true">{CURRENT}</Tag>
                <VisuallyHidden>, current</VisuallyHidden>
              </span>
              {r.line ? <span className="text-small text-text-muted">{r.line}</span> : null}
            </div>
          ) : (
            <button
              type="button"
              disabled={switching !== null}
              onClick={() => onPick(r.role)}
              className={`${CARD} motion-control hover-mix [--hover-base:var(--card-bg)] disabled:cursor-not-allowed disabled:text-text-muted`}
            >
              <span className="font-semibold">{r.title}</span>
              {switching === r.role ? <span className="text-small">{SWITCHING}</span> : null}
              {r.line ? <span className="text-small text-text-muted">{r.line}</span> : null}
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}
